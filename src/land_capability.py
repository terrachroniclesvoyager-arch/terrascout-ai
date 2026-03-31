"""
Land Capability Classification AI — USDA-inspired land capability classification
system that categorizes land into 8 classes (I-VIII) based on soil, slope,
erosion risk, drainage, and climate limitations.
Uses: SoilGrids, Open Topo Data, Open-Meteo, Overpass.
"""

import math
import logging

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
)

logger = logging.getLogger(__name__)

# USDA Land Capability Classes
CAPABILITY_CLASSES = {
    1: {"name": "Class I", "desc": "Few limitations. Widest range of uses.", "color": "#10b981",
        "uses": ["Intensive farming", "Orchards", "Gardens", "Pasture", "Forestry"]},
    2: {"name": "Class II", "desc": "Moderate limitations. Moderate conservation needed.", "color": "#22c55e",
        "uses": ["General farming", "Pasture", "Forestry", "Gardens"]},
    3: {"name": "Class III", "desc": "Severe limitations. Careful management required.", "color": "#84cc16",
        "uses": ["Selected farming", "Pasture", "Forestry"]},
    4: {"name": "Class IV", "desc": "Very severe limitations. Limited cultivation.", "color": "#f59e0b",
        "uses": ["Occasional cultivation", "Pasture", "Forestry"]},
    5: {"name": "Class V", "desc": "Unsuitable for cultivation. Wetlands, rocky.", "color": "#f97316",
        "uses": ["Pasture", "Forestry", "Wildlife habitat"]},
    6: {"name": "Class VI", "desc": "Severe limitations. Pasture/forestry only.", "color": "#ef4444",
        "uses": ["Grazing", "Forestry", "Wildlife"]},
    7: {"name": "Class VII", "desc": "Very severe limitations. Careful grazing only.", "color": "#dc2626",
        "uses": ["Light grazing", "Forestry", "Wildlife"]},
    8: {"name": "Class VIII", "desc": "Not suitable for production. Recreation/wildlife.", "color": "#991b1b",
        "uses": ["Wildlife", "Recreation", "Watershed protection"]},
}


@st.cache_data(ttl=1800)
def classify_land_capability(lat: float, lon: float) -> dict:
    """Classify land capability using multi-factor analysis."""
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=6) or {}
    weather = fetch_weather_data(lat, lon) or {}
    water = fetch_water_features(lat, lon) or {}

    limitations = []
    subclass_codes = []

    # ── Soil properties ──
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay = _sv("clay") or 20
    sand = _sv("sand") or 40
    soc = _sv("soc") or 10
    ph = _sv("phh2o") or 7.0

    # Soil limitation
    soil_limit = 0
    if clay > 60:
        soil_limit = 3
        limitations.append(f"Very high clay ({clay:.0f}%): poor drainage and workability")
        subclass_codes.append("s")
    elif clay > 40:
        soil_limit = 2
        limitations.append(f"High clay ({clay:.0f}%): limited drainage")
        subclass_codes.append("s")
    elif sand > 70:
        soil_limit = 2
        limitations.append(f"Very sandy ({sand:.0f}%): low water and nutrient retention")
        subclass_codes.append("s")

    if ph < 4.5 or ph > 9.0:
        soil_limit = max(soil_limit, 3)
        limitations.append(f"Extreme pH ({ph:.1f}): toxic to most crops")
        subclass_codes.append("s")
    elif ph < 5.5 or ph > 8.0:
        soil_limit = max(soil_limit, 1)
        limitations.append(f"Suboptimal pH ({ph:.1f}): limited crop selection")

    if soc < 3:
        soil_limit = max(soil_limit, 2)
        limitations.append(f"Very low organic matter ({soc:.1f} g/kg): poor fertility")
        subclass_codes.append("s")

    # ── Slope / Erosion ──
    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 0

    # Approximate slope
    grid_span_m = 111000 * 0.08  # ~0.04 deg radius * 2 * 111km/deg
    slope_pct = (elev_range / max(grid_span_m, 1)) * 100

    slope_limit = 0
    if slope_pct > 30:
        slope_limit = 5
        limitations.append(f"Very steep slope ({slope_pct:.0f}%): extreme erosion risk")
        subclass_codes.append("e")
    elif slope_pct > 15:
        slope_limit = 3
        limitations.append(f"Steep slope ({slope_pct:.0f}%): significant erosion risk")
        subclass_codes.append("e")
    elif slope_pct > 8:
        slope_limit = 2
        limitations.append(f"Moderate slope ({slope_pct:.0f}%): erosion management needed")
        subclass_codes.append("e")
    elif slope_pct > 3:
        slope_limit = 1
        limitations.append(f"Gentle slope ({slope_pct:.0f}%): minor erosion risk")

    # ── Drainage / Water ──
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    wetlands = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "wetland")

    drainage_limit = 0
    if wetlands > 3:
        drainage_limit = 4
        limitations.append(f"Extensive wetlands ({wetlands}): severe drainage issues")
        subclass_codes.append("w")
    elif wetlands > 0:
        drainage_limit = 2
        limitations.append(f"Wetland areas present: drainage considerations")
        subclass_codes.append("w")

    if clay > 45:
        drainage_limit = max(drainage_limit, 2)

    # ── Climate limitation ──
    daily = weather.get("daily", {})
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    valid_tmax = [t for t in temp_max if t is not None]
    valid_tmin = [t for t in temp_min if t is not None]
    avg_high = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 25
    avg_low = sum(valid_tmin) / len(valid_tmin) if valid_tmin else 10

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0
    annual_est = total_precip * (365 / max(len(valid_precip), 1)) if valid_precip else 500

    climate_limit = 0
    if avg_high > 42 or avg_low < -15:
        climate_limit = 4
        limitations.append("Extreme temperatures: severe climate limitation")
        subclass_codes.append("c")
    elif avg_high > 38 or avg_low < -5:
        climate_limit = 2
        limitations.append("Temperature extremes: limited growing season")
        subclass_codes.append("c")

    if annual_est < 200:
        climate_limit = max(climate_limit, 4)
        limitations.append(f"Arid climate (~{annual_est:.0f}mm/yr): irrigation required")
        subclass_codes.append("c")
    elif annual_est < 400:
        climate_limit = max(climate_limit, 2)
        limitations.append(f"Semi-arid (~{annual_est:.0f}mm/yr): water management needed")

    # ── Determine class ──
    max_limit = max(soil_limit, slope_limit, drainage_limit, climate_limit)

    if max_limit == 0:
        cap_class = 1
    elif max_limit == 1:
        cap_class = 2
    elif max_limit == 2:
        cap_class = 3
    elif max_limit == 3:
        cap_class = 4 if slope_limit <= 2 else 5
    elif max_limit == 4:
        cap_class = 6
    elif max_limit == 5:
        cap_class = 7
    else:
        cap_class = 8

    # Subclass code
    unique_subcodes = list(dict.fromkeys(subclass_codes))
    subclass = "".join(unique_subcodes) if unique_subcodes else ""
    full_class = f"{CAPABILITY_CLASSES[cap_class]['name']}{subclass}"

    return {
        "class": cap_class,
        "class_info": CAPABILITY_CLASSES[cap_class],
        "full_class": full_class,
        "subclass": subclass,
        "limitations": limitations,
        "factor_scores": {
            "Soil": soil_limit,
            "Slope/Erosion": slope_limit,
            "Drainage": drainage_limit,
            "Climate": climate_limit,
        },
        "raw": {
            "clay": round(clay, 1),
            "sand": round(sand, 1),
            "soc": round(soc, 1),
            "ph": round(ph, 1),
            "slope_pct": round(slope_pct, 1),
            "elev_range": round(elev_range, 0),
            "avg_elev": round(avg_elev, 0),
            "annual_precip": round(annual_est, 0),
            "avg_high": round(avg_high, 1),
            "avg_low": round(avg_low, 1),
            "wetlands": wetlands,
        },
    }


def render_land_capability_tab():
    """Render the Land Capability Classification AI tab."""
    st.markdown("## Land Capability Classification AI")
    st.caption("USDA-inspired 8-class land capability assessment")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="lc_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="lc_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="lc_lon", format="%.4f")

    if st.button("Classify Land", type="primary", use_container_width=True):
        with st.spinner("Classifying land capability..."):
            result = classify_land_capability(lat, lon)

        if not result:
            st.error("Classification failed.")
            return

        cap_class = result["class"]
        info = result["class_info"]
        full_class = result["full_class"]

        # ── Header ──
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {info['color']}22, {info['color']}44);
                    border-left:5px solid {info['color']}; border-radius:12px;
                    padding:25px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">LAND CAPABILITY CLASS</div>
                    <div style="color:{info['color']}; font-size:42px; font-weight:bold; margin:4px 0;">
                        {full_class}
                    </div>
                    <div style="color:#aaa; font-size:14px;">{info['desc']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#888; font-size:12px;">SUITABLE USES</div>
                    {''.join(f'<div style="color:#ddd; font-size:13px;">{u}</div>' for u in info['uses'])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Limitation factors ──
        st.markdown("### Limitation Factors")
        factors = result["factor_scores"]
        f_names = list(factors.keys())
        f_values = list(factors.values())
        f_colors = ["#10b981" if v == 0 else "#f59e0b" if v <= 2 else "#ef4444" for v in f_values]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=f_values,
            y=f_names,
            orientation="h",
            marker_color=f_colors,
            text=[f"Level {v}" for v in f_values],
            textposition="auto",
        ))
        fig.update_layout(
            height=250,
            margin=dict(t=10, b=20, l=120),
            xaxis=dict(range=[0, 6], title="Limitation Level (0=none, 5=severe)"),
        )
        st.plotly_chart(fig, use_container_width=True, key="lancap_pchart1")

        # ── Class scale ──
        st.markdown("### Capability Scale")
        scale_cols = st.columns(8)
        for i in range(1, 9):
            ci = CAPABILITY_CLASSES[i]
            is_current = i == cap_class
            with scale_cols[i - 1]:
                border = f"3px solid {ci['color']}" if is_current else f"1px solid {ci['color']}44"
                st.markdown(f"""
                <div style="background:{'#1a1a2e' if not is_current else ci['color'] + '33'};
                            border:{border}; border-radius:8px; padding:8px;
                            text-align:center; min-height:60px;">
                    <div style="color:{ci['color']}; font-weight:bold; font-size:16px;">
                        {'>' if is_current else ''}{ci['name'].replace('Class ', '')}{'<' if is_current else ''}
                    </div>
                    <div style="color:#888; font-size:9px;">{ci['desc'][:20]}...</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Limitations ──
        if result["limitations"]:
            st.markdown("### Identified Limitations")
            for lim in result["limitations"]:
                st.markdown(f"""
                <div style="background:#f59e0b11; border-left:3px solid #f59e0b;
                            border-radius:6px; padding:8px 12px; margin:4px 0;
                            color:#f59e0b; font-size:13px;">
                    {lim}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No significant limitations detected. Excellent land capability.")

        # ── Raw measurements ──
        st.markdown("### Site Measurements")
        raw = result["raw"]
        mc = st.columns(5)
        mc[0].metric("Clay", f"{raw['clay']}%")
        mc[1].metric("Sand", f"{raw['sand']}%")
        mc[2].metric("pH", raw["ph"])
        mc[3].metric("SOC", f"{raw['soc']} g/kg")
        mc[4].metric("Slope", f"{raw['slope_pct']}%")

        mc2 = st.columns(5)
        mc2[0].metric("Elevation", f"{raw['avg_elev']:.0f}m")
        mc2[1].metric("Elev Range", f"{raw['elev_range']:.0f}m")
        mc2[2].metric("Annual Precip", f"~{raw['annual_precip']:.0f}mm")
        mc2[3].metric("Avg High", f"{raw['avg_high']}C")
        mc2[4].metric("Wetlands", raw["wetlands"])
