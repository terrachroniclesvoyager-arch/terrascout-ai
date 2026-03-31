"""
Environmental DNA module for TerraScout AI.
Creates a unique environmental fingerprint for any location by combining
all available data into a visual 'DNA' profile with comparison capability.
"""

import hashlib
import logging
import math
import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_biodiversity,
    fetch_earthquakes,
    fetch_water_features,
    fetch_geology,
    compute_species_breakdown,
    fetch_gbif_occurrences,
    haversine_distance,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

# Global reference ranges for normalization
GLOBAL_RANGES = {
    "elevation": (0, 5000),
    "temperature": (-30, 50),
    "humidity": (0, 100),
    "precipitation_annual": (0, 3000),
    "wind_speed": (0, 80),
    "soil_clay": (0, 60),
    "soil_sand": (0, 90),
    "soil_ph": (3, 10),
    "soil_organic_c": (0, 100),
    "species_count": (0, 500),
    "observation_density": (0, 2000),
    "seismic_events": (0, 50),
    "water_features": (0, 30),
    "terrain_roughness": (0, 2000),
}


def _normalize(value, key):
    """Normalize a value to 0-1 range based on global reference."""
    lo, hi = GLOBAL_RANGES.get(key, (0, 100))
    if hi == lo:
        return 0.5
    return max(0, min(1, (value - lo) / (hi - lo)))


def _extract_dna_parameters(lat, lon):
    """Extract all environmental parameters and create DNA profile."""
    params = {}
    raw_data = {}

    # Elevation
    try:
        elev = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=7)
        center = elev.get("center_elevation", 0)
        elev_min = elev.get("min_elevation", 0)
        elev_max = elev.get("max_elevation", 0)
        if isinstance(center, (int, float)):
            params["elevation"] = center
        else:
            params["elevation"] = 0
        roughness = (elev_max - elev_min) if isinstance(elev_max, (int, float)) and isinstance(elev_min, (int, float)) else 0
        params["terrain_roughness"] = roughness
        raw_data["elevation"] = elev
    except Exception as e:
        logger.warning(f"Elevation error: {e}")
        params["elevation"] = 0
        params["terrain_roughness"] = 0

    # Weather
    try:
        wx = fetch_weather_data(lat, lon)
        current = wx.get("current", {})
        params["temperature"] = current.get("temperature_2m", 15) or 15
        params["humidity"] = current.get("relative_humidity_2m", 50) or 50
        params["wind_speed"] = current.get("wind_speed_10m", 10) or 10
        daily = wx.get("daily", {})
        precip_week = daily.get("precipitation_sum", [])
        weekly_total = sum(p for p in precip_week if p is not None) if precip_week else 0
        params["precipitation_annual"] = weekly_total * 52
        raw_data["weather"] = wx
    except Exception as e:
        logger.warning(f"Weather error: {e}")
        params["temperature"] = 15
        params["humidity"] = 50
        params["wind_speed"] = 10
        params["precipitation_annual"] = 500

    # Soil
    try:
        soil = fetch_soil_data(lat, lon)
        layers = soil.get("properties", {}).get("layers", [])
        for layer in layers:
            name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    if name == "clay":
                        params["soil_clay"] = val / 10
                    elif name == "sand":
                        params["soil_sand"] = val / 10
                    elif name == "phh2o":
                        params["soil_ph"] = val / 10
                    elif name == "soc":
                        params["soil_organic_c"] = val / 10
        raw_data["soil"] = soil
    except Exception as e:
        logger.warning(f"Soil error: {e}")

    params.setdefault("soil_clay", 25)
    params.setdefault("soil_sand", 40)
    params.setdefault("soil_ph", 6.5)
    params.setdefault("soil_organic_c", 15)

    # Biodiversity
    try:
        inat = fetch_biodiversity(lat, lon, radius_km=10)
        gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
        bio = compute_species_breakdown(inat, gbif)
        params["species_count"] = bio.get("gbif_unique_species", 0) + len(bio.get("top_species", []))
        params["observation_density"] = bio.get("inat_total", 0) + bio.get("gbif_total", 0)
        raw_data["biodiversity"] = bio
    except Exception as e:
        logger.warning(f"Biodiversity error: {e}")
        params["species_count"] = 0
        params["observation_density"] = 0

    # Seismic
    try:
        eq = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        quakes = eq.get("features", [])
        params["seismic_events"] = len(quakes)
        raw_data["earthquakes"] = eq
    except Exception as e:
        logger.warning(f"Earthquake error: {e}")
        params["seismic_events"] = 0

    # Water
    try:
        water = fetch_water_features(lat, lon, radius=5000)
        elements = water.get("elements", [])
        total_water = len(elements)
        params["water_features"] = total_water
        raw_data["water"] = water
    except Exception as e:
        logger.warning(f"Water error: {e}")
        params["water_features"] = 0

    return params, raw_data


def _generate_dna_hash(params):
    """Generate a unique DNA hash for this location's environmental profile."""
    # Quantize parameters to create stable hash
    quantized = []
    for key in sorted(GLOBAL_RANGES.keys()):
        val = params.get(key, 0)
        norm = _normalize(val, key)
        bucket = int(norm * 16)  # 16 levels per parameter
        quantized.append(f"{key}:{bucket}")
    raw = "|".join(quantized)
    return hashlib.md5(raw.encode()).hexdigest()[:12].upper()


def _dna_bar_visualization(params):
    """Create a visual DNA barcode from environmental parameters."""
    colors = {
        "elevation": "#8b5cf6",
        "temperature": "#ef4444",
        "humidity": "#3b82f6",
        "precipitation_annual": "#06b6d4",
        "wind_speed": "#94a3b8",
        "soil_clay": "#f59e0b",
        "soil_sand": "#d97706",
        "soil_ph": "#10b981",
        "soil_organic_c": "#059669",
        "species_count": "#ec4899",
        "observation_density": "#f472b6",
        "seismic_events": "#ef4444",
        "water_features": "#3b82f6",
        "terrain_roughness": "#a855f7",
    }

    bars_html = ""
    for key in sorted(GLOBAL_RANGES.keys()):
        val = params.get(key, 0)
        norm = _normalize(val, key)
        height = max(5, int(norm * 60))
        color = colors.get(key, "#64748b")
        bars_html += f'<div style="width:7%; height:{height}px; background:{color}; border-radius:2px;" title="{key}: {val:.1f}"></div>'

    return f"""
    <div style="display:flex; align-items:flex-end; gap:2px; padding:1rem;
                background:#0f172a; border-radius:8px; height:80px; justify-content:center;">
        {bars_html}
    </div>
    """


def render_environmental_dna_tab():
    """Main render function for Environmental DNA tab."""
    st.markdown("""
    <div class="tab-header violet">
        <h4>🧬 Environmental DNA</h4>
        <p>Create a unique environmental fingerprint for any location — 14 parameters, visual DNA barcode &amp; comparison</p>
    </div>
    """, unsafe_allow_html=True)

    # Mode selection
    mode = st.radio("Mode", ["Single Profile", "Compare 2 Locations"], horizontal=True, key="edna_mode")

    if mode == "Single Profile":
        col1, col2 = st.columns(2)
        with col1:
            preset = st.selectbox("Preset", list(ANALYSIS_PRESETS.keys()), key="edna_preset")
        preset_data = ANALYSIS_PRESETS.get(preset)
        d_lat = preset_data["lat"] if preset_data else 41.90
        d_lon = preset_data["lon"] if preset_data else 12.50
        with col2:
            c1, c2 = st.columns(2)
            with c1:
                lat = st.number_input("Lat", -90.0, 90.0, d_lat, step=0.01, key="edna_lat", format="%.4f")
            with c2:
                lon = st.number_input("Lon", -180.0, 180.0, d_lon, step=0.01, key="edna_lon", format="%.4f")

        if st.button("🧬 Generate Environmental DNA", type="primary", use_container_width=True):
            with st.spinner("Scanning environmental parameters..."):
                params, raw_data = _extract_dna_parameters(lat, lon)
            dna_hash = _generate_dna_hash(params)
            st.session_state["edna_result"] = {
                "params": params, "hash": dna_hash, "lat": lat, "lon": lon,
            }

        if "edna_result" in st.session_state:
            r = st.session_state["edna_result"]
            params = r["params"]
            dna_hash = r["hash"]

            st.markdown("---")

            # DNA Hash
            st.markdown(f"""
            <div style="text-align:center; padding:1.5rem; background:#1e293b; border-radius:12px;
                        border:2px solid #8b5cf6; margin-bottom:1rem;">
                <div style="color:#8b5cf6; font-size:0.9rem; font-weight:600;">ENVIRONMENTAL DNA</div>
                <div style="font-family:monospace; font-size:2rem; color:#e2e8f0; letter-spacing:4px;
                            margin:0.5rem 0;">{dna_hash}</div>
                <div style="color:#64748b; font-size:0.8rem;">({r['lat']:.4f}, {r['lon']:.4f})</div>
            </div>
            """, unsafe_allow_html=True)

            # DNA Barcode
            st.markdown("#### DNA Barcode")
            st.markdown(_dna_bar_visualization(params), unsafe_allow_html=True)

            # Radar profile
            st.markdown("#### Environmental Profile")
            labels = [k.replace("_", " ").title() for k in sorted(GLOBAL_RANGES.keys())]
            values = [_normalize(params.get(k, 0), k) * 100 for k in sorted(GLOBAL_RANGES.keys())]
            values_closed = values + [values[0]]
            labels_closed = labels + [labels[0]]

            fig = go.Figure(data=go.Scatterpolar(
                r=values_closed, theta=labels_closed,
                fill="toself", line_color="#8b5cf6",
                fillcolor="rgba(139, 92, 246, 0.15)",
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=450, margin=dict(t=30, b=30, l=80, r=80),
            )
            st.plotly_chart(fig, use_container_width=True, key="envdna_pchart1")

            # Parameter table
            st.markdown("#### Raw Parameters")
            param_rows = []
            for key in sorted(GLOBAL_RANGES.keys()):
                val = params.get(key, 0)
                norm = _normalize(val, key)
                lo, hi = GLOBAL_RANGES[key]
                param_rows.append({
                    "Parameter": key.replace("_", " ").title(),
                    "Value": round(val, 2),
                    "Normalized (%)": round(norm * 100, 1),
                    "Global Range": f"{lo} - {hi}",
                })
            df = pd.DataFrame(param_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Export
            csv = df.to_csv(index=False)
            st.download_button("📥 Download DNA Profile (CSV)", data=csv,
                               file_name=f"env_dna_{dna_hash}.csv", mime="text/csv")

    else:
        # Compare mode
        st.markdown("**Location A**")
        ca1, ca2 = st.columns(2)
        with ca1:
            lat_a = st.number_input("Lat A", -90.0, 90.0, 41.90, step=0.01, key="edna_lat_a", format="%.4f")
        with ca2:
            lon_a = st.number_input("Lon A", -180.0, 180.0, 12.50, step=0.01, key="edna_lon_a", format="%.4f")

        st.markdown("**Location B**")
        cb1, cb2 = st.columns(2)
        with cb1:
            lat_b = st.number_input("Lat B", -90.0, 90.0, 36.11, step=0.01, key="edna_lat_b", format="%.4f")
        with cb2:
            lon_b = st.number_input("Lon B", -180.0, 180.0, -112.11, step=0.01, key="edna_lon_b", format="%.4f")

        if st.button("🧬 Compare DNA Profiles", type="primary", use_container_width=True):
            with st.spinner("Scanning Location A..."):
                params_a, _ = _extract_dna_parameters(lat_a, lon_a)
            with st.spinner("Scanning Location B..."):
                params_b, _ = _extract_dna_parameters(lat_b, lon_b)

            hash_a = _generate_dna_hash(params_a)
            hash_b = _generate_dna_hash(params_b)

            # Similarity score
            diffs = []
            for key in sorted(GLOBAL_RANGES.keys()):
                na = _normalize(params_a.get(key, 0), key)
                nb = _normalize(params_b.get(key, 0), key)
                diffs.append(abs(na - nb))
            similarity = round((1 - sum(diffs) / len(diffs)) * 100, 1)

            st.session_state["edna_compare"] = {
                "a": params_a, "b": params_b,
                "hash_a": hash_a, "hash_b": hash_b,
                "similarity": similarity,
                "lat_a": lat_a, "lon_a": lon_a,
                "lat_b": lat_b, "lon_b": lon_b,
            }

        if "edna_compare" in st.session_state:
            r = st.session_state["edna_compare"]
            params_a, params_b = r["a"], r["b"]

            st.markdown("---")

            # Similarity badge
            sim = r["similarity"]
            sim_color = "#10b981" if sim > 80 else "#06b6d4" if sim > 60 else "#f59e0b" if sim > 40 else "#ef4444"
            st.markdown(f"""
            <div style="text-align:center; padding:1rem; background:#1e293b; border-radius:12px;
                        margin-bottom:1rem;">
                <span style="color:{sim_color}; font-size:2.5rem; font-weight:900;">{sim}%</span>
                <span style="color:#94a3b8; font-size:1rem;"> Environmental Similarity</span>
            </div>
            """, unsafe_allow_html=True)

            # Side-by-side DNA
            dc1, dc2 = st.columns(2)
            with dc1:
                st.markdown(f"**Location A** `{r['hash_a']}`")
                st.markdown(_dna_bar_visualization(params_a), unsafe_allow_html=True)
            with dc2:
                st.markdown(f"**Location B** `{r['hash_b']}`")
                st.markdown(_dna_bar_visualization(params_b), unsafe_allow_html=True)

            # Overlay radar
            st.markdown("#### Profile Comparison")
            labels = [k.replace("_", " ").title() for k in sorted(GLOBAL_RANGES.keys())]
            vals_a = [_normalize(params_a.get(k, 0), k) * 100 for k in sorted(GLOBAL_RANGES.keys())]
            vals_b = [_normalize(params_b.get(k, 0), k) * 100 for k in sorted(GLOBAL_RANGES.keys())]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals_a + [vals_a[0]], theta=labels + [labels[0]],
                fill="toself", name="Location A", line_color="#06b6d4", opacity=0.6,
            ))
            fig.add_trace(go.Scatterpolar(
                r=vals_b + [vals_b[0]], theta=labels + [labels[0]],
                fill="toself", name="Location B", line_color="#f59e0b", opacity=0.6,
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=450, margin=dict(t=30, b=30, l=80, r=80),
            )
            st.plotly_chart(fig, use_container_width=True, key="envdna_pchart2")

            # Difference table
            st.markdown("#### Parameter Differences")
            diff_rows = []
            for key in sorted(GLOBAL_RANGES.keys()):
                va = params_a.get(key, 0)
                vb = params_b.get(key, 0)
                diff = vb - va
                diff_rows.append({
                    "Parameter": key.replace("_", " ").title(),
                    "Location A": round(va, 2),
                    "Location B": round(vb, 2),
                    "Difference": round(diff, 2),
                })
            st.dataframe(pd.DataFrame(diff_rows), use_container_width=True, hide_index=True)
