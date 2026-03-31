# -*- coding: utf-8 -*-
"""
Global Biodiversity Heatmap module for TerraScout AI.
Visualizes worldwide biodiversity hotspots using GBIF occurrence data
and iNaturalist research-grade observations, rendered as a viridis-colored
heatmap showing species density across the entire planet.
"""

import io
import logging
import streamlit as st
try:
    import folium
    from folium.plugins import HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import html as html_module
import requests
from streamlit.components.v1 import html as st_html

logger = logging.getLogger(__name__)

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


# Enhanced UI components
try:
    from src.ui_components import info_card, success_banner, stats_grid
    UI_COMPONENTS_AVAILABLE = True
except ImportError:
    UI_COMPONENTS_AVAILABLE = False

# ── Theme ──
_BG, _SURFACE, _CARD = "#0a0e1a", "#111827", "#1a2235"
_BORDER, _TEXT, _TEXT2 = "#2a3550", "#e8ecf4", "#8b97b0"

# ── Viridis palette (CSS hex) ──
VIRIDIS = [
    "#440154", "#482878", "#3e4989", "#31688e", "#26828e",
    "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725",
]

# ── GBIF / iNaturalist API endpoints ──
GBIF_OCC_API = "https://api.gbif.org/v1/occurrence/search"
INAT_API = "https://api.inaturalist.org/v1"

# ── Biodiversity exploration modes ──
MAP_MODES = [
    "All Species Heatmap",
    "Mammals Diversity",
    "Birds Diversity",
    "Reptiles & Amphibians",
    "Fish & Marine Life",
    "Insects & Arthropods",
    "Plants & Flora",
    "Fungi & Lichens",
    "Endangered Species",
    "Endemic Hotspots",
]

MODE_CONFIG = {
    "All Species Heatmap": {
        "color": "#1f9e89", "icon": "globe",
        "desc": "Global species occurrence density — a worldwide heatmap of all life.",
        "gbif_params": {},
        "inat_params": {},
    },
    "Mammals Diversity": {
        "color": "#f59e0b", "icon": "paw",
        "desc": "Mammal species density worldwide — from mice to whales.",
        "gbif_params": {"taxonKey": 359},  # Mammalia
        "inat_params": {"iconic_taxa": "Mammalia"},
    },
    "Birds Diversity": {
        "color": "#3b82f6", "icon": "feather",
        "desc": "Avian biodiversity hotspots — world's most bird-rich areas.",
        "gbif_params": {"taxonKey": 212},  # Aves
        "inat_params": {"iconic_taxa": "Aves"},
    },
    "Reptiles & Amphibians": {
        "color": "#10b981", "icon": "frog",
        "desc": "Herpetofauna diversity — reptiles and amphibians across the globe.",
        "gbif_params": {"taxonKey": 358},  # Reptilia
        "inat_params": {"iconic_taxa": "Reptilia"},
    },
    "Fish & Marine Life": {
        "color": "#06b6d4", "icon": "fish",
        "desc": "Marine and freshwater fish species density.",
        "gbif_params": {"taxonKey": 204},  # Actinopterygii (ray-finned fishes)
        "inat_params": {"iconic_taxa": "Actinopterygii"},
    },
    "Insects & Arthropods": {
        "color": "#ec4899", "icon": "bug",
        "desc": "Insect and arthropod species observations worldwide.",
        "gbif_params": {"taxonKey": 216},  # Insecta
        "inat_params": {"iconic_taxa": "Insecta"},
    },
    "Plants & Flora": {
        "color": "#22c55e", "icon": "leaf",
        "desc": "Plant species diversity — flowering plants, ferns, trees, and more.",
        "gbif_params": {"taxonKey": 6},  # Plantae
        "inat_params": {"iconic_taxa": "Plantae"},
    },
    "Fungi & Lichens": {
        "color": "#a855f7", "icon": "mushroom",
        "desc": "Fungal diversity — mushrooms, molds, lichens across ecosystems.",
        "gbif_params": {"taxonKey": 5},  # Fungi
        "inat_params": {"iconic_taxa": "Fungi"},
    },
    "Endangered Species": {
        "color": "#ef4444", "icon": "alert",
        "desc": "IUCN threatened species occurrence — critically endangered to vulnerable globally.",
        "gbif_params": {"iucnRedListCategory": "CR,EN,VU"},
        "inat_params": {"threatened": "true"},
    },
    "Endemic Hotspots": {
        "color": "#f97316", "icon": "star",
        "desc": "Global areas with highest concentrations of unique endemic species.",
        "gbif_params": {},
        "inat_params": {"endemic": "true"},
    },
}

# =====================================================================
# GBIF GLOBAL DATA FETCHING (ENHANCED WITH PAGINATION)
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_gbif_global(mode: str, limit: int = 1500) -> list:
    """
    Fetch species occurrences globally from GBIF with pagination support.
    Can fetch up to 50,000+ records by making multiple requests.
    """
    cfg = MODE_CONFIG[mode]

    # GBIF max limit per request is 300
    max_per_page = 300
    total_pages = (limit + max_per_page - 1) // max_per_page  # Ceiling division

    all_points = []

    try:
        for page in range(total_pages):
            offset = page * max_per_page
            page_limit = min(max_per_page, limit - offset)

            params = {
                "hasCoordinate": "true",
                "limit": page_limit,
                "offset": offset,
            }
            params.update(cfg.get("gbif_params", {}))

            resp = requests.get(GBIF_OCC_API, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for occ in data.get("results", []):
                dlat = occ.get("decimalLatitude")
                dlon = occ.get("decimalLongitude")
                if dlat is not None and dlon is not None:
                    all_points.append({
                        "lat": dlat, "lon": dlon,
                        "species": occ.get("species", occ.get("scientificName", "Unknown")),
                        "kingdom": occ.get("kingdom", "Unknown"),
                        "country": occ.get("country", ""),
                    })

            # Stop if we got fewer results than expected (no more data)
            if len(data.get("results", [])) < page_limit:
                break

        return all_points
    except Exception as e:
        logger.warning("GBIF Error: %s", e)
        return all_points  # Return what we got so far

@st.cache_data(ttl=3600)
def _fetch_inat_global(mode: str, limit: int = 1000) -> list:
    """
    Fetch species observations globally from iNaturalist with pagination.
    iNaturalist max per_page is 200, so we make multiple requests.
    """
    cfg = MODE_CONFIG[mode]

    max_per_page = 200
    total_pages = min((limit + max_per_page - 1) // max_per_page, 10)  # Max 10 pages = 2000 records

    all_points = []

    try:
        for page in range(1, total_pages + 1):
            params = {
                "per_page": max_per_page,
                "page": page,
                "quality_grade": "research",
                "order": "desc",
                "order_by": "created_at",  # Get recent observations
            }
            params.update(cfg.get("inat_params", {}))

            resp = requests.get(f"{INAT_API}/observations", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                break

            for obs in results:
                loc = obs.get("location")
                if not loc:
                    continue
                parts = loc.split(",")
                if len(parts) == 2:
                    try:
                        olat, olon = float(parts[0]), float(parts[1])
                    except ValueError:
                        continue
                    taxon = obs.get("taxon", {})
                    all_points.append({
                        "lat": olat, "lon": olon,
                        "species": taxon.get("name", "Unknown"),
                        "kingdom": taxon.get("iconic_taxon_name", "Unknown"),
                    })

        return all_points
    except Exception as e:
        logger.warning("iNat Error: %s", e)
        return all_points


# =====================================================================
# BIODIVERSITY HOTSPOTS STRATEGIC SAMPLING
# =====================================================================
BIODIVERSITY_HOTSPOTS = [
    # Amazon Basin
    {"name": "Amazon", "lat": -3.4653, "lon": -62.2159, "radius": 500},
    # Madagascar
    {"name": "Madagascar", "lat": -18.7669, "lon": 46.8691, "radius": 300},
    # Southeast Asian Rainforests
    {"name": "Borneo", "lat": 0.9619, "lon": 114.5548, "radius": 300},
    {"name": "Sumatra", "lat": -0.5897, "lon": 101.3431, "radius": 250},
    # Central Africa
    {"name": "Congo Basin", "lat": -2.8770, "lon": 23.6561, "radius": 400},
    # Coral Triangle
    {"name": "Philippines", "lat": 12.8797, "lon": 121.7740, "radius": 300},
    # Atlantic Forest
    {"name": "Atlantic Forest", "lat": -22.9068, "lon": -43.1729, "radius": 250},
    # Eastern Himalayas
    {"name": "Eastern Himalayas", "lat": 27.9881, "lon": 86.9250, "radius": 200},
    # Western Ghats
    {"name": "Western Ghats", "lat": 15.2993, "lon": 74.1240, "radius": 200},
    # Mesoamerica
    {"name": "Central America", "lat": 9.7489, "lon": -83.7534, "radius": 250},
]

@st.cache_data(ttl=3600)
def _fetch_strategic_hotspots(mode: str, points_per_hotspot: int = 500) -> list:
    """
    Fetch biodiversity data strategically from known hotspots.
    This ensures we get high-density areas for better heatmap contrast.
    """
    cfg = MODE_CONFIG[mode]
    all_points = []

    for hotspot in BIODIVERSITY_HOTSPOTS:
        # Query GBIF for this hotspot
        params = {
            "hasCoordinate": "true",
            "limit": points_per_hotspot,
            "decimalLatitude": f"{hotspot['lat']-5},{hotspot['lat']+5}",  # ±5 degrees
            "decimalLongitude": f"{hotspot['lon']-5},{hotspot['lon']+5}",
        }
        params.update(cfg.get("gbif_params", {}))

        try:
            resp = requests.get(GBIF_OCC_API, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()

            for occ in data.get("results", []):
                dlat = occ.get("decimalLatitude")
                dlon = occ.get("decimalLongitude")
                if dlat is not None and dlon is not None:
                    all_points.append({
                        "lat": dlat, "lon": dlon,
                        "species": occ.get("species", occ.get("scientificName", "Unknown")),
                        "kingdom": occ.get("kingdom", "Unknown"),
                        "country": occ.get("country", ""),
                        "hotspot": hotspot["name"],
                    })
        except Exception as e:
            logger.warning("Hotspot %s Error: %s", hotspot['name'], e)
            continue

    return all_points


# =====================================================================
# ENHANCED VIRIDIS HEATMAP BUILDER WITH DENSITY WEIGHTING
# =====================================================================
def _calculate_density_weights(points: list) -> list:
    """
    Calculate density-based weights for each point to create better contrast.
    Points in dense clusters get higher weights (red/yellow in heatmap).
    """
    try:
        from scipy.spatial import cKDTree
        import numpy as np
    except ImportError:
        # Fallback if scipy not available
        return [[p["lat"], p["lon"], 1.0] for p in points]

    if len(points) < 2:
        return [[p["lat"], p["lon"], 1.0] for p in points]

    # Build KD-tree for fast nearest neighbor search
    coords = np.array([[p["lat"], p["lon"]] for p in points])
    tree = cKDTree(coords)

    # For each point, count neighbors within 2 degrees (~200km)
    radius = 2.0
    heat_data = []

    for i, p in enumerate(points):
        # Query neighbors within radius
        neighbors = tree.query_ball_point([p["lat"], p["lon"]], radius)
        density = len(neighbors)

        # Weight based on density (log scale to avoid extreme values)
        weight = min(np.log1p(density) / 5.0, 3.0)  # Max weight 3.0

        heat_data.append([p["lat"], p["lon"], weight])

    return heat_data


def _build_heatmap(points: list, zoom: int = 2, use_density_weights: bool = True):
    """
    Build a global folium heatmap with viridis color gradient.
    Now with enhanced density weighting for better contrast.
    """
    # We recenter on the equator since it's global
    m = folium.Map(
        location=[0.0, 0.0],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        min_zoom=1,
        max_bounds=True
    )

    if points:
        # Calculate density-weighted heat data
        if use_density_weights and len(points) > 100:
            heat_data = _calculate_density_weights(points)
        else:
            heat_data = [[p["lat"], p["lon"], 1.0] for p in points]

        HeatMap(
            heat_data,
            radius=25,  # INCREASED from 15 for better visibility
            blur=18,     # REDUCED from 25 for sharper hotspots
            max_zoom=13, # INCREASED from 1 for proper intensity scaling
            min_opacity=0.3,
            gradient={
                0.0: "#440154",   # Deep purple
                0.1: "#482878",   # Purple
                0.2: "#3e4989",   # Blue-purple
                0.35: "#26828e",  # Teal
                0.5: "#1f9e89",   # Green-teal
                0.65: "#6ece58",  # Yellow-green
                0.8: "#b5de2b",   # Yellow
                0.95: "#fde725",  # Bright yellow
                1.0: "#ff0000",   # RED for highest density hotspots
            },
        ).add_to(m)

    return m


# =====================================================================
# MAIN RENDER
# =====================================================================

# Rate limiting configuration
if rate_limiter:
    api_config = get_rate_limit_config("gbif")

def render_biodiversity_global_maps_tab():
    """Render the Global Biodiversity Heatmap tab."""

    header_html = (
        '<div class="tab-header emerald">'
        '<h4>🌍 Global Biodiversity Viridis Heatmap</h4>'
        '<p>Visualize species density and biological hotspots worldwide using a viridis gradient — '
        'from deep purple (low) to bright yellow (high biodiversity).</p></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Viridis legend
    gradient_css = ", ".join(VIRIDIS)
    st.markdown(
        f'<div style="display:flex;align-items:center;margin:8px 0;">'
        f'<span style="color:#8b97b0;font-size:0.8em;margin-right:8px;">Low / None</span>'
        f'<div style="flex:1;height:12px;border-radius:6px;'
        f'background:linear-gradient(to right, {gradient_css});"></div>'
        f'<span style="color:#8b97b0;font-size:0.8em;margin-left:8px;">High Biodiversity</span></div>',
        unsafe_allow_html=True,
    )

    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        mode = st.selectbox("Global Biodiversity Category", MAP_MODES, key="bioglob_mode")
    with col2:
         data_source = st.selectbox("Data Source", ["GBIF + iNaturalist", "GBIF only", "iNaturalist only"],
                                key="bioglob_source")
    with col3:
         sample_size = st.slider("Global Sample Size", 1000, 50000, 10000, 1000, key="bioglob_limit",
                                 help="Number of global records to plot. 10k+ recommended for good contrast.")

    # Strategic sampling option
    use_hotspots = st.checkbox(
        "🔥 Use Strategic Hotspot Sampling",
        value=True,
        key="bioglob_hotspots",
        help="Focus sampling on known biodiversity hotspots (Amazon, Madagascar, Borneo, etc.) for better heatmap contrast and red zones."
    )

    cfg = MODE_CONFIG[mode]
    st.markdown(
        f"<p style='color:{_TEXT2};'>{html_module.escape(cfg['desc'])}</p>",
        unsafe_allow_html=True,
    )

    # Info about strategic sampling
    if use_hotspots and UI_COMPONENTS_AVAILABLE:
        info_card(
            "Strategic Hotspot Sampling Active",
            f"Focusing on <strong>{len(BIODIVERSITY_HOTSPOTS)}</strong> known biodiversity hotspots "
            "(Amazon, Madagascar, Borneo, Congo, Philippines, Atlantic Forest, Himalayas, etc.) "
            "to ensure rich data density and visible red zones in the heatmap. "
            f"Target: <strong>{len(BIODIVERSITY_HOTSPOTS) * 500:,}+</strong> records from hotspots + "
            f"<strong>{sample_size - (len(BIODIVERSITY_HOTSPOTS) * 500):,}</strong> global records.",
            "🔥",
            "#ef4444"
        )

    if st.button("🌿 Generate Worldwide Heatmap", key="bioglob_go",
                 type="primary", use_container_width=True):
        st.session_state.bioglob_params = {
            "mode": mode, "source": data_source, "limit": sample_size, "hotspots": use_hotspots
        }

    if "bioglob_params" not in st.session_state:
        if UI_COMPONENTS_AVAILABLE:
            info_card(
                "Get Started",
                "Select a biodiversity category, adjust sample size (10k+ recommended), "
                "and click <strong>Generate Worldwide Heatmap</strong> to visualize global species distribution with rich color contrast.",
                "🌿",
                "#10b981"
            )
        else:
            st.info("Select a category, then click **Generate Worldwide Heatmap** to visualize global species distribution.")
        return

    bp = st.session_state.bioglob_params

    # Fetch global data with progress tracking
    all_points = []

    # Strategic hotspot sampling (recommended)
    if bp.get("hotspots", True):
        with st.spinner("🔥 Fetching data from biodiversity hotspots (Amazon, Madagascar, Borneo, etc.)..."):
            hotspot_pts = _fetch_strategic_hotspots(bp["mode"], points_per_hotspot=500)
            all_points.extend(hotspot_pts)
            st.success(f"✅ Loaded {len(hotspot_pts):,} records from {len(BIODIVERSITY_HOTSPOTS)} biodiversity hotspots")

    # Additional global sampling
    remaining_limit = max(0, bp["limit"] - len(all_points))
    if remaining_limit > 0:
        progress_bar = st.progress(0.0, text="Loading global biodiversity data...")

        if bp["source"] in ("GBIF + iNaturalist", "GBIF only"):
            progress_bar.progress(0.3, text="📡 Querying GBIF global database...")
            gbif_pts = _fetch_gbif_global(bp["mode"], limit=remaining_limit)
            all_points.extend(gbif_pts)
            progress_bar.progress(0.7, text=f"✓ GBIF: {len(gbif_pts):,} records loaded")

        if bp["source"] in ("GBIF + iNaturalist", "iNaturalist only"):
            progress_bar.progress(0.8, text="🦋 Querying iNaturalist observations...")
            inat_limit = min(2000, remaining_limit // 2)  # Up to 2000 from iNat
            inat_pts = _fetch_inat_global(bp["mode"], limit=inat_limit)
            all_points.extend(inat_pts)
            progress_bar.progress(0.95, text=f"✓ iNaturalist: {len(inat_pts):,} records loaded")

        progress_bar.progress(1.0, text="✅ Data loading complete!")
        progress_bar.empty()

    if not all_points:
        st.warning("No global biodiversity observations found for this category.")
        return

    # Show success banner with total
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1.25rem 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        font-weight: 600;
        font-size: 1.05rem;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.25);
        text-align: center;
    ">
        ✅ Successfully loaded <strong>{len(all_points):,}</strong> biodiversity records for heatmap generation
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ──
    st.markdown("---")
    unique_species = set(p.get("species", "") for p in all_points if p.get("species") and p.get("species") != "Unknown")
    kingdoms = {}
    for p in all_points:
        k = p.get("kingdom", "Unknown")
        kingdoms[k] = kingdoms.get(k, 0) + 1

    # Use modern stats grid if available
    if UI_COMPONENTS_AVAILABLE:
        overview_stats = [
            {
                "label": "Global Points Plotted",
                "value": f"{len(all_points):,}",
                "icon": "🌍",
                "color": "#06b6d4"
            },
            {
                "label": "Unique Species",
                "value": f"{len(unique_species):,}",
                "icon": "🦋",
                "color": "#10b981"
            },
            {
                "label": "Taxonomic Groups",
                "value": f"{len(kingdoms)}",
                "icon": "🧬",
                "color": "#8b5cf6"
            }
        ]
        stats_grid(overview_stats, columns=3)
    else:
        cols = st.columns(3)
        cols[0].metric("Plotted Global Points", len(all_points))
        cols[1].metric("Unique Species Identified", len(unique_species))
        cols[2].metric("Taxonomic Groups", len(kingdoms))

    # Show hotspot contribution breakdown if strategic sampling was used
    if bp.get("hotspots", False):
        hotspot_counts = {}
        for p in all_points:
            hs = p.get("hotspot")
            if hs:
                hotspot_counts[hs] = hotspot_counts.get(hs, 0) + 1

        if hotspot_counts:
            with st.expander(f"🔥 Biodiversity Hotspot Contributions ({len(hotspot_counts)} active regions)", expanded=False):
                hotspot_df = pd.DataFrame([
                    {"Hotspot Region": k, "Records": v, "Percentage": f"{(v/len(all_points)*100):.1f}%"}
                    for k, v in sorted(hotspot_counts.items(), key=lambda x: -x[1])
                ])
                st.dataframe(hotspot_df, use_container_width=True, hide_index=True)

    # ── Map ──
    st.markdown("---")
    st.markdown(
        f"<div style='margin: 1rem 0;'>"
        f"<span style='color:{cfg['color']};font-weight:600;font-size:1.1rem;'>"
        f"● Global Heatmap: {html_module.escape(bp['mode'])}</span><br>"
        f"<span style='color:#8b97b0;font-size:0.9rem;'>Density-weighted visualization: "
        f"<span style='color:#440154'>◼</span> Purple = Low density | "
        f"<span style='color:#1f9e89'>◼</span> Teal = Medium | "
        f"<span style='color:#fde725'>◼</span> Yellow = High | "
        f"<span style='color:#ff0000'>◼</span> Red = Extreme biodiversity hotspots</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.spinner("🎨 Generating density-weighted heatmap with viridis gradient..."):
        m = _build_heatmap(all_points, zoom=2, use_density_weights=True)
    st_html(m._repr_html_(), height=600)

    # ── Kingdom breakdown chart ──
    st.markdown("---")
    st.markdown("#### Global Taxonomic Distribution")
    if kingdoms:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor("#0a0e1a")

        # Donut chart
        ax1.set_facecolor("#0a0e1a")
        sorted_kingdoms = sorted(kingdoms.items(), key=lambda x: -x[1])
        labels = [k for k, v in sorted_kingdoms]
        sizes = [v for k, v in sorted_kingdoms]
        colors_pie = VIRIDIS[:len(labels)] if len(labels) <= len(VIRIDIS) else (
            VIRIDIS * (len(labels) // len(VIRIDIS) + 1))[:len(labels)]
        wedges, texts, autotexts = ax1.pie(
            sizes, labels=None, autopct="%1.0f%%",
            colors=colors_pie, startangle=90,
            pctdistance=0.8, wedgeprops=dict(width=0.4, edgecolor="#0a0e1a"),
        )
        for t in autotexts:
            t.set_color("#e8ecf4")
            t.set_fontsize(8)
        ax1.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5),
                   fontsize=8, facecolor="#0a0e1a", edgecolor="#2a3550",
                   labelcolor="#8b97b0")
        ax1.set_title("Kingdom Distribution", color="#e8ecf4", fontsize=11)

        # Bar chart
        ax2.set_facecolor("#0a0e1a")
        ax2.barh(range(len(labels)), sizes, color=colors_pie, alpha=0.85)
        ax2.set_yticks(range(len(labels)))
        ax2.set_yticklabels(labels, color="#8b97b0", fontsize=9)
        ax2.set_xlabel("Observations", color="#8b97b0", fontsize=10)
        ax2.tick_params(colors="#8b97b0", labelsize=9)
        for spine in ax2.spines.values():
            spine.set_color("#2a3550")
        ax2.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.5)
        ax2.invert_yaxis()
        ax2.set_title("Observation Counts", color="#e8ecf4", fontsize=11)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ── Top species list ──
    species_counts = {}
    for p in all_points:
        sp = p.get("species", "Unknown")
        if sp and sp != "Unknown":
            species_counts[sp] = species_counts.get(sp, 0) + 1
    top_species = sorted(species_counts.items(), key=lambda x: -x[1])[:20]

    if top_species:
        st.markdown(f"#### 🏆 Top 20 Global Flagship Species ({bp['mode']})")
        sp_df = pd.DataFrame(top_species, columns=["Species", "Records Sampled"])
        sp_df.index = range(1, len(sp_df) + 1)
        st.dataframe(sp_df, use_container_width=True)

    # ── Data table & download ──
    st.markdown("---")
    rows = [{
        "Species": p.get("species", ""),
        "Latitude": round(p["lat"], 5),
        "Longitude": round(p["lon"], 5),
        "Kingdom": p.get("kingdom", ""),
        "Country": p.get("country", ""),
    } for p in all_points]
    df = pd.DataFrame(rows)
    with st.expander(f"Full Global Sample Data Table ({len(df)} records)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        f"Download {len(rows)} Biodiv Records (CSV)",
        data=buf.getvalue(),
        file_name=f"global_biodiversity_{bp['mode'].lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="bioglob_dl",
    )
