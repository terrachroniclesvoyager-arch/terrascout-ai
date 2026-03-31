"""
Wildfire Tracker module for TerraScout AI.
Uses NASA FIRMS (Fire Information for Resource Management System) open data
to display active fire detections from MODIS and VIIRS satellites.
"""

import io
import math
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


# NASA FIRMS open CSV endpoints (no API key needed for country/region data)
FIRMS_CSV_BASE = "https://firms.modaps.eosdis.nasa.gov/data/active_fire"

# Alternative: use the FIRMS map API for recent data by area
FIRMS_MAP_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Fire Radiative Power (FRP) color scale
FRP_COLORS = {
    "low": "#f59e0b",       # < 10 MW
    "moderate": "#f97316",  # 10-50 MW
    "high": "#ef4444",      # 50-200 MW
    "extreme": "#dc2626",   # > 200 MW
}


def _frp_color(frp: float) -> str:
    if frp < 10:
        return FRP_COLORS["low"]
    elif frp < 50:
        return FRP_COLORS["moderate"]
    elif frp < 200:
        return FRP_COLORS["high"]
    return FRP_COLORS["extreme"]


def _frp_radius(frp: float) -> float:
    if frp < 10:
        return 3
    elif frp < 50:
        return 5
    elif frp < 200:
        return 8
    return 12


# Predefined regions with known fire activity data
REGIONS = {
    "Global - Recent": {"desc": "Recent global fire detections"},
    "Mediterranean": {"lat": 38.0, "lon": 15.0, "radius": 1500,
                      "desc": "Southern Europe, North Africa, Middle East"},
    "Western USA": {"lat": 38.0, "lon": -120.0, "radius": 1000,
                    "desc": "California, Oregon, Washington, Nevada"},
    "Amazon Basin": {"lat": -5.0, "lon": -60.0, "radius": 2000,
                     "desc": "Brazilian Amazon and surroundings"},
    "Sub-Saharan Africa": {"lat": 0.0, "lon": 25.0, "radius": 3000,
                           "desc": "Central and Southern Africa"},
    "Southeast Asia": {"lat": 5.0, "lon": 110.0, "radius": 2000,
                       "desc": "Indonesia, Malaysia, Thailand, Philippines"},
    "Australia": {"lat": -25.0, "lon": 135.0, "radius": 2000,
                  "desc": "Continental Australia"},
    "Siberia": {"lat": 60.0, "lon": 100.0, "radius": 3000,
                "desc": "Russian Siberia boreal fires"},
}

# Countries with ISO codes for FIRMS data
COUNTRY_FIRE_DATA = {
    "USA": "USA", "Canada": "CAN", "Brazil": "BRA", "Australia": "AUS",
    "Russia": "RUS", "Indonesia": "IDN", "India": "IND", "China": "CHN",
    "Italy": "ITA", "Spain": "ESP", "Portugal": "PRT", "Greece": "GRC",
    "Turkey": "TUR", "France": "FRA", "South Africa": "ZAF",
}


@st.cache_data(ttl=300)
def fetch_firms_data(source: str = "VIIRS_SNPP_NRT",
                     days: int = 2,
                     area_bbox: tuple = None) -> pd.DataFrame:
    """
    Fetch active fire data from FIRMS.
    Uses the open CSV endpoints that don't require an API key.
    Falls back to generating sample data if the API is unavailable.
    """
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("nasa_firms")
    try:
        # Try the FIRMS open data CSV endpoint
        if area_bbox:
            west, south, east, north = area_bbox
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/FIRMS_OPEN/{source}/{west},{south},{east},{north}/{days}"
        else:
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/FIRMS_OPEN/{source}/-180,-90,180,90/{days}"

        resp = requests.get(url, timeout=30, headers={"User-Agent": "TerraScoutAI/1.0"})
        if resp.status_code == 200 and len(resp.text) > 100:
            df = pd.read_csv(io.StringIO(resp.text))
            if len(df) > 0:
                return df
    except Exception:
        pass

    # If FIRMS API fails, try USDA/NIFC active fire data
    try:
        url = "https://opendata.arcgis.com/datasets/5da472c6d27b4b67970acc7b5044c862_0.csv"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            if len(df) > 0:
                # Normalize column names
                col_map = {}
                for c in df.columns:
                    cl = c.lower()
                    if "lat" in cl:
                        col_map[c] = "latitude"
                    elif "lon" in cl or "long" in cl:
                        col_map[c] = "longitude"
                    elif "bright" in cl or "frp" in cl:
                        col_map[c] = "frp"
                    elif "date" in cl or "time" in cl:
                        col_map[c] = "acq_date"
                    elif "conf" in cl:
                        col_map[c] = "confidence"
                df = df.rename(columns=col_map)
                return df
    except Exception:
        pass

    return pd.DataFrame()


@st.cache_data(ttl=600)
def get_fire_stats_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """Compute fire count stats by country from fire data."""
    if df.empty:
        return pd.DataFrame()

    # If no country column, estimate from coordinates
    if "country_id" not in df.columns and "latitude" in df.columns:
        return pd.DataFrame()

    stats = df.groupby("country_id").agg(
        fire_count=("latitude", "count"),
        avg_frp=("frp", "mean") if "frp" in df.columns else ("latitude", "count"),
    ).reset_index().sort_values("fire_count", ascending=False)

    return stats


def render_fire_tracker_tab():
    """Main render function for the Wildfire Tracker tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>Wildfire Tracker</h4>
        <p>Track active fire detections from NASA FIRMS satellites (MODIS/VIIRS) &mdash; near real-time fire data worldwide.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Search Parameters
    # ══════════════════════════════════════════
    st.markdown("#### Search Parameters")

    col1, col2 = st.columns(2)
    with col1:
        satellite = st.selectbox("Satellite Source", [
            "VIIRS_SNPP_NRT",
            "VIIRS_NOAA20_NRT",
            "MODIS_NRT",
        ], key="fire_sat", help="VIIRS has higher resolution; MODIS has longer history")

    with col2:
        days = st.selectbox("Time Period", [1, 2, 3, 5, 7, 10], index=1,
                            key="fire_days", help="Number of days to look back")

    # Region selection
    region_name = st.selectbox("Region", list(REGIONS.keys()), key="fire_region")
    region = REGIONS[region_name]

    st.markdown(f'<p style="color:#8b97b0; font-size:0.85rem;">{region["desc"]}</p>',
                unsafe_allow_html=True)

    # Custom bbox
    with st.expander("Custom Bounding Box", expanded=False):
        bcol1, bcol2, bcol3, bcol4 = st.columns(4)
        with bcol1:
            bb_west = st.number_input("West", value=-180.0, format="%.2f", key="fire_west")
        with bcol2:
            bb_south = st.number_input("South", value=-90.0, format="%.2f", key="fire_south")
        with bcol3:
            bb_east = st.number_input("East", value=180.0, format="%.2f", key="fire_east")
        with bcol4:
            bb_north = st.number_input("North", value=90.0, format="%.2f", key="fire_north")
        use_custom_bbox = st.checkbox("Use custom bbox", key="fire_use_bbox")

    if st.button("Track Wildfires", key="fire_search", width="stretch"):
        bbox = None
        if use_custom_bbox:
            bbox = (bb_west, bb_south, bb_east, bb_north)
        elif region_name != "Global - Recent" and "lat" in region:
            # Convert region center+radius to bbox
            lat, lon, r = region["lat"], region["lon"], region.get("radius", 1000)
            dlat = r / 111.0
            dlon = r / (111.0 * max(0.01, abs(math.cos(math.radians(lat)))))
            bbox = (lon - dlon, lat - dlat, lon + dlon, lat + dlat)

        st.session_state.fire_params = {
            "satellite": satellite,
            "days": days,
            "bbox": bbox,
            "region": region_name,
        }

    if "fire_params" not in st.session_state:
        st.info("Select a region and time period, then click Track to view fire detections.")
        return

    fp = st.session_state.fire_params

    # ══════════════════════════════════════════
    # SECTION 2: Fire Data
    # ══════════════════════════════════════════
    with st.spinner("Fetching fire detection data from NASA FIRMS..."):
        df = fetch_firms_data(fp["satellite"], fp["days"], fp.get("bbox"))

    if df.empty:
        st.warning("No fire data available for this region/period. The FIRMS API may be temporarily unavailable, or there are no active fires in this area.")
        st.info("Try: 'Global - Recent' region, or expand the time period to 7-10 days.")
        return

    # Normalize column names
    df.columns = [c.lower().strip() for c in df.columns]

    lat_col = next((c for c in df.columns if "lat" in c), None)
    lon_col = next((c for c in df.columns if "lon" in c), None)

    if not lat_col or not lon_col:
        st.warning("Fire data format not recognized. Missing latitude/longitude columns.")
        return

    total_fires = len(df)

    st.markdown("---")
    st.markdown("#### Fire Detection Summary")

    # Stats
    frp_col = next((c for c in df.columns if "frp" in c or "bright" in c), None)
    conf_col = next((c for c in df.columns if "conf" in c), None)
    date_col = next((c for c in df.columns if "date" in c or "acq_date" in c), None)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Active Fires", f"{total_fires:,}")
    with c2:
        st.metric("Satellite", fp["satellite"].replace("_NRT", ""))
    with c3:
        if frp_col and frp_col in df.columns:
            avg_frp = df[frp_col].mean()
            st.metric("Avg FRP", f"{avg_frp:.1f} MW")
        else:
            st.metric("Period", f"{fp['days']} days")
    with c4:
        if frp_col and frp_col in df.columns:
            max_frp = df[frp_col].max()
            st.metric("Max FRP", f"{max_frp:.1f} MW")
        else:
            st.metric("Region", fp["region"])

    # ══════════════════════════════════════════
    # SECTION 3: Fire Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Fire Detection Map")

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:#f59e0b; font-size:0.8rem;">● Low FRP (&lt;10 MW)</span>
        <span style="color:#f97316; font-size:0.8rem;">● Moderate (10-50 MW)</span>
        <span style="color:#ef4444; font-size:0.8rem;">● High (50-200 MW)</span>
        <span style="color:#dc2626; font-size:0.8rem;">● Extreme (&gt;200 MW)</span>
    </div>
    """, unsafe_allow_html=True)

    # Center map on data
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=4, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    # Add satellite imagery layer
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Satellite",
        overlay=False,
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Add fire markers (limit to 2000 for performance)
    display_df = df.head(2000)
    for _, row in display_df.iterrows():
        lat = row[lat_col]
        lon = row[lon_col]
        frp = row.get(frp_col, 5) if frp_col else 5
        try:
            if pd.isna(frp):
                frp = 5.0
            else:
                frp = float(frp)
        except (TypeError, ValueError):
            frp = 5.0

        conf = row.get(conf_col, "—") if conf_col else "—"
        acq_date = row.get(date_col, "—") if date_col else "—"

        popup_html = f"""
        <div style="max-width:180px;">
            <strong>Fire Detection</strong><br/>
            <span style="font-size:0.85rem;">FRP: {frp:.1f} MW</span><br/>
            <span style="font-size:0.8rem;">Confidence: {conf}</span><br/>
            <span style="font-size:0.8rem;">Date: {acq_date}</span><br/>
            <span style="font-size:0.75rem;">{lat:.4f}, {lon:.4f}</span>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=_frp_radius(frp),
            color=_frp_color(frp),
            fill=True,
            fill_color=_frp_color(frp),
            fill_opacity=0.5,
            weight=1,
            popup=folium.Popup(popup_html, max_width=200),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    if total_fires > 2000:
        st.caption(f"Showing 2,000 of {total_fires:,} fire detections on map.")

    # ══════════════════════════════════════════
    # SECTION 4: Charts & Analysis
    # ══════════════════════════════════════════
    st.markdown("---")
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        st.markdown("#### Fire Intensity (FRP Distribution)")
        if frp_col and frp_col in df.columns:
            frp_vals = df[frp_col].dropna().values
            if len(frp_vals) > 0:
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor("#0a0e1a")
                ax.set_facecolor("#0a0e1a")
                ax.hist(frp_vals, bins=30, color="#f97316", edgecolor="#0a0e1a", alpha=0.8)
                ax.set_xlabel("Fire Radiative Power (MW)", color="#8b97b0", fontsize=10)
                ax.set_ylabel("Count", color="#8b97b0", fontsize=10)
                ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
                ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
                ax.set_axisbelow(True)
                for spine in ax.spines.values():
                    spine.set_color("#2a3550")
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)
        else:
            st.info("FRP data not available in this dataset.")

    with col_chart2:
        st.markdown("#### Fires by Day")
        if date_col and date_col in df.columns:
            daily = df.groupby(date_col).size().reset_index(name="count")
            if len(daily) > 0:
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                fig2.patch.set_facecolor("#0a0e1a")
                ax2.set_facecolor("#0a0e1a")
                ax2.bar(range(len(daily)), daily["count"].values, color="#ef4444", alpha=0.8)
                ax2.set_xticks(range(len(daily)))
                ax2.set_xticklabels(daily[date_col].values, rotation=45, ha="right")
                ax2.set_ylabel("Fire Count", color="#8b97b0", fontsize=10)
                ax2.tick_params(axis="both", colors="#8b97b0", labelsize=8)
                ax2.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
                ax2.set_axisbelow(True)
                for spine in ax2.spines.values():
                    spine.set_color("#2a3550")
                fig2.tight_layout()
                st.pyplot(fig2)
                plt.close(fig2)
        else:
            st.info("Date information not available.")

    # ══════════════════════════════════════════
    # SECTION 5: Data Table & Download
    # ══════════════════════════════════════════
    st.markdown("---")

    # Show relevant columns
    display_cols = [c for c in [lat_col, lon_col, frp_col, conf_col, date_col]
                    if c and c in df.columns]
    if not display_cols:
        display_cols = list(df.columns[:6])

    with st.expander(f"Fire Data Table ({total_fires} detections)", expanded=False):
        st.dataframe(df[display_cols].head(500), width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {total_fires:,} Fire Detections (CSV)",
        data=csv_buf.getvalue(),
        file_name="fire_detections.csv",
        mime="text/csv",
        key="fire_download",
    )
