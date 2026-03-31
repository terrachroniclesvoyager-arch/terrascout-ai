"""
Biodiversity / iNaturalist tab module for Pocket GIS AI.
Uses the iNaturalist v1 API (free, no API key) to search observations and species.
"""

import io
import html as html_module
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


INAT_API = "https://api.inaturalist.org/v1"

# Taxon ID shortcuts for common groups
TAXON_GROUPS = {
    "All": None,
    "Plants": 47126,
    "Birds": 3,
    "Mammals": 40151,
    "Insects": 47158,
    "Reptiles": 26036,
    "Amphibians": 20978,
    "Fish": 47178,
    "Fungi": 47170,
    "Arachnids": 47119,
    "Mollusks": 47115,
}

# Colors per taxon for map markers
TAXON_COLORS = {
    "Plantae": "#10b981",
    "Aves": "#06b6d4",
    "Mammalia": "#8b5cf6",
    "Insecta": "#f59e0b",
    "Reptilia": "#ef4444",
    "Amphibia": "#ec4899",
    "Actinopterygii": "#3b82f6",
    "Fungi": "#a855f7",
    "Arachnida": "#f97316",
    "Mollusca": "#14b8a6",
}


@st.cache_data(ttl=300)
def search_observations(lat: float, lng: float, radius_km: int = 10,
                        taxon_id: int = None, per_page: int = 200) -> dict:
    """Search observations near a point."""
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("inaturalist")
    params = {
        "lat": lat,
        "lng": lng,
        "radius": radius_km,
        "per_page": min(per_page, 200),
        "order": "desc",
        "order_by": "observed_on",
        "quality_grade": "research",
    }
    if taxon_id:
        params["taxon_id"] = taxon_id

    try:
        resp = requests.get(f"{INAT_API}/observations", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"total_results": 0, "results": [], "error": str(e)}


@st.cache_data(ttl=600)
def get_species_counts(lat: float, lng: float, radius_km: int = 10,
                       taxon_id: int = None) -> dict:
    """Get species counts for an area."""
    params = {
        "lat": lat,
        "lng": lng,
        "radius": radius_km,
        "quality_grade": "research",
    }
    if taxon_id:
        params["taxon_id"] = taxon_id

    try:
        resp = requests.get(f"{INAT_API}/observations/species_counts", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"total_results": 0, "results": [], "error": str(e)}


def _get_photo_url(obs: dict, size: str = "medium") -> str:
    """Extract photo URL from observation."""
    photos = obs.get("photos", [])
    if photos:
        url = photos[0].get("url", "")
        return url.replace("square", size)
    return ""


def _get_taxon_color(obs: dict) -> str:
    """Get marker color based on iconic taxon."""
    taxon = obs.get("taxon", {})
    iconic = taxon.get("iconic_taxon_name", "")
    return TAXON_COLORS.get(iconic, "#8b97b0")


def render_biodiversity_tab():
    """Main render function for the Biodiversity tab."""

    # Header
    st.markdown("""
    <div class="tab-header emerald">
        <h4>Biodiversity Explorer</h4>
        <p>Search wildlife observations from iNaturalist &mdash; the world's largest biodiversity database. Filter by taxon, view on map, download CSV.</p>
    </div>
    """, unsafe_allow_html=True)

    # Controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        lat = st.number_input("Latitude", value=41.8902, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="bio_lat")
    with col2:
        lng = st.number_input("Longitude", value=12.4922, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="bio_lng")
    with col3:
        radius = st.slider("Radius (km)", 1, 50, 10, key="bio_radius")
    with col4:
        taxon_name = st.selectbox("Taxon Group", list(TAXON_GROUPS.keys()), key="bio_taxon")

    taxon_id = TAXON_GROUPS[taxon_name]

    if st.button("Search Observations", key="bio_search", width="stretch"):
        st.session_state.bio_search_params = {
            "lat": lat, "lng": lng, "radius": radius, "taxon_id": taxon_id
        }

    if "bio_search_params" not in st.session_state:
        st.info("Set coordinates and radius, then click Search to explore biodiversity data.")
        return

    params = st.session_state.bio_search_params

    # Fetch data
    with st.spinner("Fetching observations from iNaturalist..."):
        obs_data = search_observations(
            params["lat"], params["lng"], params["radius"], params.get("taxon_id")
        )
        species_data = get_species_counts(
            params["lat"], params["lng"], params["radius"], params.get("taxon_id")
        )

    if obs_data.get("error"):
        st.error(f"API Error: {obs_data['error']}")
        return

    observations = obs_data.get("results", [])
    total_obs = obs_data.get("total_results", 0)
    species_list = species_data.get("results", [])
    total_species = species_data.get("total_results", 0)

    # Stats
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Observations", f"{total_obs:,}")
    with c2:
        st.metric("Species Found", f"{total_species:,}")
    with c3:
        st.metric("Shown Here", f"{len(observations)}")

    st.markdown("---")

    # Map with markers
    m = folium.Map(
        location=[params["lat"], params["lng"]],
        zoom_start=11,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark",
        name="Dark Base",
    ).add_to(m)

    # Search radius circle
    folium.Circle(
        location=[params["lat"], params["lng"]],
        radius=params["radius"] * 1000,
        color="#06b6d4",
        fill=True,
        fill_opacity=0.05,
        weight=1,
    ).add_to(m)

    # Add observation markers
    for obs in observations:
        loc = obs.get("location", "")
        if not loc:
            continue
        try:
            obs_lat, obs_lng = [float(x) for x in loc.split(",")]
        except (ValueError, AttributeError):
            continue

        taxon = obs.get("taxon", {})
        common = taxon.get("preferred_common_name", taxon.get("name", "Unknown"))
        scientific = taxon.get("name", "")
        color = _get_taxon_color(obs)
        photo = _get_photo_url(obs, "small")

        popup_html = f"""
        <div style="max-width:200px;">
            <strong>{html_module.escape(common)}</strong><br/>
            <em style="font-size:0.8rem;">{html_module.escape(scientific)}</em><br/>
        """
        if photo:
            popup_html += f'<img src="{html_module.escape(photo)}" style="width:100%;border-radius:6px;margin-top:4px;"/>'
        popup_html += "</div>"

        folium.CircleMarker(
            location=[obs_lat, obs_lng],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup_html, max_width=220),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # Two columns: species list + observation cards
    col_species, col_obs = st.columns([1, 1])

    with col_species:
        st.markdown("#### Top Species")
        if species_list:
            top_species = species_list[:20]
            species_rows = []
            for sp in top_species:
                taxon = sp.get("taxon", {})
                species_rows.append({
                    "Common Name": taxon.get("preferred_common_name", "—"),
                    "Scientific Name": taxon.get("name", "—"),
                    "Count": sp.get("count", 0),
                    "Group": taxon.get("iconic_taxon_name", "—"),
                })
            df_species = pd.DataFrame(species_rows)
            st.dataframe(df_species, width="stretch", hide_index=True)
        else:
            st.info("No species data available.")

    with col_obs:
        st.markdown("#### Recent Observations")
        if observations:
            for obs in observations[:12]:
                taxon = obs.get("taxon", {})
                common = taxon.get("preferred_common_name", taxon.get("name", "Unknown"))
                scientific = taxon.get("name", "")
                date = obs.get("observed_on_string", obs.get("observed_on", "—"))
                photo = _get_photo_url(obs, "small")
                user = obs.get("user", {}).get("login", "—")

                img_html = ""
                if photo:
                    img_html = f'<img src="{html_module.escape(photo)}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;margin-right:0.75rem;"/>'

                st.markdown(f"""
                <div class="bio-card" style="display:flex;align-items:center;margin-bottom:0.5rem;">
                    {img_html}
                    <div>
                        <div style="color:#e8ecf4;font-weight:600;font-size:0.85rem;">{html_module.escape(common)}</div>
                        <div style="color:#8b97b0;font-size:0.75rem;font-style:italic;">{html_module.escape(scientific)}</div>
                        <div style="color:#5a6580;font-size:0.7rem;">{html_module.escape(date)} by {html_module.escape(user)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No observations found in this area.")

    # CSV Download
    if observations:
        st.markdown("---")
        rows = []
        for obs in observations:
            taxon = obs.get("taxon", {})
            loc = obs.get("location", "")
            lat_obs, lng_obs = "", ""
            if loc:
                try:
                    lat_obs, lng_obs = loc.split(",")
                except ValueError:
                    pass
            rows.append({
                "id": obs.get("id"),
                "common_name": taxon.get("preferred_common_name", ""),
                "scientific_name": taxon.get("name", ""),
                "group": taxon.get("iconic_taxon_name", ""),
                "latitude": lat_obs,
                "longitude": lng_obs,
                "observed_on": obs.get("observed_on", ""),
                "user": obs.get("user", {}).get("login", ""),
                "quality_grade": obs.get("quality_grade", ""),
            })
        df_export = pd.DataFrame(rows)
        csv_buf = io.StringIO()
        df_export.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download {len(rows)} Observations (CSV)",
            data=csv_buf.getvalue(),
            file_name="inaturalist_observations.csv",
            mime="text/csv",
            key="bio_download",
        )
