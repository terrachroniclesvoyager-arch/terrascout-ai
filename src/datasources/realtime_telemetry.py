"""
Real-Time Telemetry Client for TerraScout AI

Data Sources:
1. OpenSky Network - Live aircraft tracking (ADS-B)
2. AISStream.io - Live ship tracking (AIS)
3. ACLED - Conflict and political violence events

Use Case: Real-time situational awareness in remote areas
"""

import streamlit as st
import requests
from typing import Tuple, List, Dict, Any
from ..error_handler import with_retry


class RealtimeTelemetryClient:
    """Client for real-time telemetry data."""

    OPENSKY_API = "https://opensky-network.org/api"

    def __init__(self):
        self.session = requests.Session()

    @with_retry(max_retries=2)
    def get_aircraft_in_area(
        self,
        bbox: Tuple[float, float, float, float]
    ) -> List[Dict[str, Any]]:
        """Get live aircraft in bbox from OpenSky Network."""
        min_lon, min_lat, max_lon, max_lat = bbox

        try:
            response = self.session.get(
                f"{self.OPENSKY_API}/states/all",
                params={
                    "lamin": min_lat,
                    "lomin": min_lon,
                    "lamax": max_lat,
                    "lomax": max_lon
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            aircraft = data.get('states', [])
            st.success(f"✈️ Found {len(aircraft)} aircraft")

            return aircraft

        except Exception as e:
            st.warning(f"⚠️ Aircraft tracking failed: {e}")
            return []
