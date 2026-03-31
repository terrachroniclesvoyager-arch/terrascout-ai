"""
Biodiversity APIs Client for TerraScout AI

Data Sources:
1. GBIF - Global Biodiversity Information Facility
2. Map of Life - Species distribution models
3. UN Biodiversity Lab - Conservation data

Use Case: Assess biodiversity richness and endangered species in remote areas
"""

import streamlit as st
import requests
from typing import Tuple, Dict, Any
from ..error_handler import with_retry


class BiodiversityClient:
    """Client for biodiversity and species data."""

    GBIF_API = "https://api.gbif.org/v1"

    def __init__(self):
        self.session = requests.Session()

    @with_retry(max_retries=2)
    def get_species_richness(
        self,
        bbox: Tuple[float, float, float, float]
    ) -> Dict[str, Any]:
        """Get species richness data for bbox from GBIF."""
        min_lon, min_lat, max_lon, max_lat = bbox

        try:
            # GBIF occurrence search
            response = self.session.get(
                f"{self.GBIF_API}/occurrence/search",
                params={
                    "decimalLatitude": f"{min_lat},{max_lat}",
                    "decimalLongitude": f"{min_lon},{max_lon}",
                    "limit": 300
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            species_count = data.get('count', 0)
            st.success(f"🦋 Found {species_count:,} species occurrences")

            return {"species_count": species_count, "data": data}

        except Exception as e:
            st.warning(f"⚠️ Biodiversity API failed: {e}")
            return {"species_count": 0}
