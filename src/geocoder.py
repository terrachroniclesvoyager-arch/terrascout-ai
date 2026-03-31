"""
Geocoder tab module for Pocket GIS AI.
Forward, reverse, and batch geocoding via Nominatim (OpenStreetMap).
"""

import time
import io
import logging

import requests
import pandas as pd
import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

try:
    from streamlit_folium import st_folium
    HAS_ST_FOLIUM = True
except ImportError:
    HAS_ST_FOLIUM = False

logger = logging.getLogger(__name__)

# ─── NOMINATIM CONFIG ───
NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "PocketGISAI/1.0"}
ACCENT = "#06b6d4"


# ═══════════════════════════════════════════════════════════════
#  GEOCODING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def forward_geocode(query: str) -> list:
    """Forward geocode an address string via Nominatim.

    Returns a list of result dicts, each containing:
        lat, lon, display_name, address (detailed breakdown)
    """
    try:
        resp = requests.get(
            f"{NOMINATIM_BASE}/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 5,
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        time.sleep(1)  # respect rate limit

        results = []
        for item in resp.json():
            results.append({
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "display_name": item.get("display_name", ""),
                "address": item.get("address", {}),
                "type": item.get("type", ""),
                "category": item.get("category", ""),
            })
        return results

    except requests.RequestException as exc:
        logger.error("Forward geocode failed: %s", exc)
        return []


@st.cache_data(ttl=3600)
def reverse_geocode(lat: float, lon: float) -> dict:
    """Reverse geocode a coordinate pair via Nominatim.

    Returns a dict with display_name, address details, or empty dict on failure.
    """
    try:
        resp = requests.get(
            f"{NOMINATIM_BASE}/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "addressdetails": 1,
            },
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        time.sleep(1)  # respect rate limit

        data = resp.json()
        if "error" in data:
            return {}

        return {
            "lat": float(data.get("lat", lat)),
            "lon": float(data.get("lon", lon)),
            "display_name": data.get("display_name", ""),
            "address": data.get("address", {}),
            "type": data.get("type", ""),
            "category": data.get("category", ""),
        }

    except requests.RequestException as exc:
        logger.error("Reverse geocode failed: %s", exc)
        return {}


def batch_geocode(addresses: list) -> list:
    """Geocode a list of address strings sequentially (1 req/sec).

    Displays a Streamlit progress bar. NOT cached because it uses
    st.progress internally and results depend on external state.

    Returns a list of dicts (one per address). Failed lookups have
    lat/lon as None.
    """
    results = []
    total = len(addresses)
    progress = st.progress(0, text="Geocoding...")

    for idx, addr in enumerate(addresses):
        progress.progress(
            (idx + 1) / total,
            text=f"Geocoding {idx + 1}/{total}: {addr[:60]}..."
        )
        hits = forward_geocode(addr)
        if hits:
            best = hits[0]
            results.append({
                "address_input": addr,
                "lat": best["lat"],
                "lon": best["lon"],
                "display_name": best["display_name"],
            })
        else:
            results.append({
                "address_input": addr,
                "lat": None,
                "lon": None,
                "display_name": "",
            })
        # forward_geocode already sleeps 1s, but add guard for cache hits
        time.sleep(0.1)

    progress.empty()
    return results


# ═══════════════════════════════════════════════════════════════
#  MAP HELPERS
# ═══════════════════════════════════════════════════════════════

def _make_map(center=None, zoom=13):
    """Create a folium map with CartoDB dark tiles."""
    if center is None:
        center = [41.9028, 12.4964]
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)
    return m


def _add_marker(m, lat, lon, popup_text=""):
    """Add a cyan marker with popup to a folium map."""
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color="lightblue", icon="info-sign"),
    ).add_to(m)
    # Also add a cyan circle for emphasis
    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color=ACCENT,
        fill=True,
        fill_color=ACCENT,
        fill_opacity=0.6,
        weight=2,
    ).add_to(m)


def _render_map(m, height=450):
    """Render folium map using streamlit_folium if available, else components.html."""
    if HAS_ST_FOLIUM:
        try:
            st_folium(m, height=height, width=None, returned_objects=[], key="geocd_folium_map")
            return
        except Exception:
            pass
    components.html(m._repr_html_(), height=height)


# ═══════════════════════════════════════════════════════════════
#  ADDRESS CARD HTML
# ═══════════════════════════════════════════════════════════════

def _address_card(display_name, lat=None, lon=None):
    """Return glass-card HTML for an address result."""
    coord_line = ""
    if lat is not None and lon is not None:
        coord_line = (
            f'<p style="margin:0.4rem 0 0; color:#8b97b0; font-size:0.85rem;">'
            f'<strong style="color:{ACCENT};">Lat:</strong> {lat:.6f} &nbsp; '
            f'<strong style="color:{ACCENT};">Lon:</strong> {lon:.6f}</p>'
        )
    return f"""
    <div class="glass-card" style="margin:0.75rem 0;">
        <p style="margin:0; color:#e8ecf4; font-size:0.95rem;">{display_name}</p>
        {coord_line}
    </div>
    """


def _address_details_expander(address_dict):
    """Show full address breakdown inside an expander."""
    if not address_dict:
        return
    with st.expander("Full Address Details"):
        for key, value in address_dict.items():
            st.markdown(
                f"**{key.replace('_', ' ').title()}**: {value}"
            )


# ═══════════════════════════════════════════════════════════════
#  MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_geocoder_tab():
    """Render the complete Geocoder tab UI."""

    st.markdown("""
    <div class="tab-header pink">
        <h4>Geocoder</h4>
        <p>Forward, reverse, and batch geocoding via Nominatim (OpenStreetMap). Convert addresses to coordinates and vice versa.</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio(
        "Geocoding Mode",
        ["Forward (Address \u2192 Coords)", "Reverse (Coords \u2192 Address)", "Batch (CSV Upload)"],
        horizontal=True,
        key="geo_mode",
    )

    st.markdown("---")

    # ─── FORWARD ────────────────────────────────────────────
    if mode.startswith("Forward"):
        _render_forward_mode()

    # ─── REVERSE ────────────────────────────────────────────
    elif mode.startswith("Reverse"):
        _render_reverse_mode()

    # ─── BATCH ──────────────────────────────────────────────
    else:
        _render_batch_mode()


# ═══════════════════════════════════════════════════════════════
#  FORWARD MODE
# ═══════════════════════════════════════════════════════════════

def _render_forward_mode():
    address_query = st.text_input(
        "Address or Place Name",
        placeholder="e.g. Colosseo, Roma, Italia",
        key="geo_fwd_input",
    )
    search_clicked = st.button("Search", key="geo_fwd_btn", width="stretch")

    if search_clicked and address_query.strip():
        with st.spinner("Searching..."):
            results = forward_geocode(address_query.strip())

        if not results:
            st.warning("No results found. Try a different query.")
            return

        st.session_state["geo_fwd_results"] = results

    results = st.session_state.get("geo_fwd_results", [])
    if not results:
        return

    st.success(f"Found {len(results)} result(s)")

    # Show first result on map
    first = results[0]
    m = _make_map(center=[first["lat"], first["lon"]], zoom=15)
    for r in results:
        _add_marker(m, r["lat"], r["lon"], popup_text=r["display_name"])
    _render_map(m)

    # Result cards
    for idx, r in enumerate(results):
        st.markdown(
            _address_card(r["display_name"], r["lat"], r["lon"]),
            unsafe_allow_html=True,
        )
        _address_details_expander(r.get("address", {}))


# ═══════════════════════════════════════════════════════════════
#  REVERSE MODE
# ═══════════════════════════════════════════════════════════════

def _render_reverse_mode():
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude", value=41.890200, format="%.6f", key="geo_rev_lat")
    with col_lon:
        lon = st.number_input("Longitude", value=12.492200, format="%.6f", key="geo_rev_lon")

    lookup_clicked = st.button("Lookup", key="geo_rev_btn", width="stretch")

    if lookup_clicked:
        with st.spinner("Looking up address..."):
            result = reverse_geocode(lat, lon)

        if not result:
            st.warning("No address found at this location.")
            return

        st.session_state["geo_rev_result"] = result

    result = st.session_state.get("geo_rev_result")
    if not result:
        return

    # Address card
    st.markdown(
        _address_card(result["display_name"], result.get("lat"), result.get("lon")),
        unsafe_allow_html=True,
    )
    _address_details_expander(result.get("address", {}))

    # Map
    m = _make_map(center=[result["lat"], result["lon"]], zoom=16)
    _add_marker(m, result["lat"], result["lon"], popup_text=result["display_name"])
    _render_map(m)


# ═══════════════════════════════════════════════════════════════
#  BATCH MODE
# ═══════════════════════════════════════════════════════════════

def _render_batch_mode():
    uploaded = st.file_uploader(
        "Upload CSV with an 'address' column",
        type=["csv"],
        key="geo_batch_upload",
    )

    if uploaded is None:
        st.info("Upload a CSV file containing a column named **address**.")
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        return

    # Validate column
    col_lower = {c.lower().strip(): c for c in df.columns}
    if "address" not in col_lower:
        st.error(
            "CSV must contain a column named **address**. "
            f"Found columns: {', '.join(df.columns)}"
        )
        return

    address_col = col_lower["address"]
    addresses = df[address_col].dropna().astype(str).tolist()
    n = len(addresses)

    if n == 0:
        st.warning("No addresses found in the CSV.")
        return

    st.info(f"Found **{n}** addresses in column '{address_col}'.")

    if n > 50:
        st.warning(
            f"You have {n} addresses. Nominatim rate-limits to 1 request/second, "
            f"so this will take at least **{n} seconds** (~{n // 60} min). "
            "Consider reducing the list or using a commercial geocoding API for large batches."
        )

    geocode_clicked = st.button("Geocode All", key="geo_batch_btn", width="stretch")

    if geocode_clicked:
        geo_results = batch_geocode(addresses)
        st.session_state["geo_batch_results"] = geo_results
        st.session_state["geo_batch_source_df"] = df
        st.session_state["geo_batch_address_col"] = address_col

    geo_results = st.session_state.get("geo_batch_results")
    if not geo_results:
        return

    source_df = st.session_state.get("geo_batch_source_df", df)
    address_col = st.session_state.get("geo_batch_address_col", "address")

    # Build enriched dataframe
    geo_df = pd.DataFrame(geo_results)
    enriched = source_df.copy()
    enriched["lat"] = geo_df["lat"].values[: len(enriched)]
    enriched["lon"] = geo_df["lon"].values[: len(enriched)]
    enriched["display_name"] = geo_df["display_name"].values[: len(enriched)]

    # Stats
    found = enriched["lat"].notna().sum()
    failed = len(enriched) - found
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total", len(enriched))
    with c2:
        st.metric("Geocoded", int(found))
    with c3:
        st.metric("Failed", int(failed))

    # Dataframe
    st.dataframe(enriched, width="stretch", hide_index=True)

    # Map with all markers
    valid = enriched.dropna(subset=["lat", "lon"])
    if not valid.empty:
        center_lat = valid["lat"].mean()
        center_lon = valid["lon"].mean()
        m = _make_map(center=[center_lat, center_lon], zoom=5)
        for _, row in valid.iterrows():
            popup = str(row.get("display_name", row.get(address_col, "")))
            _add_marker(m, row["lat"], row["lon"], popup_text=popup)
        _render_map(m, height=500)
    else:
        st.warning("No addresses could be geocoded. Check the input data.")

    # Download enriched CSV
    csv_buffer = io.StringIO()
    enriched.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Enriched CSV",
        data=csv_buffer.getvalue(),
        file_name="geocoded_results.csv",
        mime="text/csv",
        key="geo_batch_download",
    )
