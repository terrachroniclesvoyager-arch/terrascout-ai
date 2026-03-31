"""
API Health Dashboard
Monitors status and health of all external APIs used by TerraScout AI
"""

import streamlit as st
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import rate limiter
try:
    from src.rate_limiter import rate_limiter, display_rate_limit_dashboard
    from src.app_logger import log_api_call
except:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None
    display_rate_limit_dashboard = lambda: None


# API Configuration
API_ENDPOINTS = {
    "NASA NEO": {
        "url": "https://api.nasa.gov/neo/rest/v1/feed",
        "params": {"api_key": "DEMO_KEY", "start_date": "2024-01-01", "end_date": "2024-01-02"},
        "timeout": 10,
        "category": "Space & Astronomy"
    },
    "NASA APOD": {
        "url": "https://api.nasa.gov/planetary/apod",
        "params": {"api_key": "DEMO_KEY"},
        "timeout": 10,
        "category": "Space & Astronomy"
    },
    "Open-Meteo Weather": {
        "url": "https://api.open-meteo.com/v1/forecast",
        "params": {"latitude": 40.7128, "longitude": -74.006, "current": "temperature_2m"},
        "timeout": 10,
        "category": "Weather & Climate"
    },
    "USGS Earthquake": {
        "url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
        "params": {"format": "geojson", "limit": 1},
        "timeout": 10,
        "category": "Earth Science"
    },
    "iNaturalist": {
        "url": "https://api.inaturalist.org/v1/observations",
        "params": {"lat": 40.7128, "lng": -74.006, "per_page": 1},
        "timeout": 10,
        "category": "Biodiversity"
    },
    "GBIF": {
        "url": "https://api.gbif.org/v1/occurrence/search",
        "params": {"limit": 1},
        "timeout": 10,
        "category": "Biodiversity"
    },
    "Nominatim OSM": {
        "url": "https://nominatim.openstreetmap.org/search",
        "params": {"q": "London", "format": "json", "limit": 1},
        "timeout": 10,
        "category": "Geocoding",
        "headers": {"User-Agent": "TerraScout-AI/1.0"}
    },
    "Open-Elevation": {
        "url": "https://api.open-elevation.com/api/v1/lookup",
        "params": {"locations": "40.7128,-74.006"},
        "timeout": 10,
        "category": "Earth Science"
    },
    "OpenAQ Air Quality": {
        "url": "https://api.openaq.org/v2/latest",
        "params": {"limit": 1, "coordinates": "40.7128,-74.006", "radius": 50000},
        "timeout": 10,
        "category": "Environmental"
    },
    "ISS Location": {
        "url": "http://api.open-notify.org/iss-now.json",
        "params": {},
        "timeout": 5,
        "category": "Space & Astronomy"
    }
}


def check_api_health(api_name: str, config: Dict) -> Dict:
    """
    Check health of a single API endpoint.

    Returns:
        {
            "name": str,
            "status": "online" | "slow" | "offline",
            "response_time_ms": float,
            "error": Optional[str],
            "category": str
        }
    """
    start_time = time.time()

    try:
        headers = config.get("headers", {})
        response = requests.get(
            config["url"],
            params=config.get("params", {}),
            headers=headers,
            timeout=config.get("timeout", 10)
        )

        duration_ms = (time.time() - start_time) * 1000

        # Determine status based on response time
        if response.status_code == 200:
            if duration_ms < 1000:
                status = "online"
            elif duration_ms < 3000:
                status = "slow"
            else:
                status = "very_slow"
        else:
            status = "error"

        return {
            "name": api_name,
            "status": status,
            "response_time_ms": duration_ms,
            "status_code": response.status_code,
            "error": None if response.status_code == 200 else f"HTTP {response.status_code}",
            "category": config.get("category", "Other")
        }

    except requests.Timeout:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "name": api_name,
            "status": "timeout",
            "response_time_ms": duration_ms,
            "status_code": None,
            "error": "Request timed out",
            "category": config.get("category", "Other")
        }

    except requests.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "name": api_name,
            "status": "offline",
            "response_time_ms": duration_ms,
            "status_code": None,
            "error": str(e)[:100],
            "category": config.get("category", "Other")
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return {
            "name": api_name,
            "status": "error",
            "response_time_ms": duration_ms,
            "status_code": None,
            "error": str(e)[:100],
            "category": config.get("category", "Other")
        }


@st.cache_data(ttl=300)  # Cache for 5 minutes
def check_all_apis() -> List[Dict]:
    """
    Check health of all APIs in parallel.

    Returns:
        List of health check results
    """
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(check_api_health, name, config): name
            for name, config in API_ENDPOINTS.items()
        }

        for future in as_completed(futures):
            try:
                result = future.result(timeout=15)
                results.append(result)
            except Exception as e:
                api_name = futures[future]
                results.append({
                    "name": api_name,
                    "status": "error",
                    "response_time_ms": 0,
                    "status_code": None,
                    "error": f"Health check failed: {str(e)}",
                    "category": API_ENDPOINTS[api_name].get("category", "Other")
                })

    return results


def get_status_color(status: str) -> str:
    """Get color for status indicator."""
    colors = {
        "online": "#10b981",      # Green
        "slow": "#f59e0b",        # Orange
        "very_slow": "#ef4444",   # Red
        "timeout": "#ef4444",     # Red
        "offline": "#6b7280",     # Gray
        "error": "#dc2626"        # Dark red
    }
    return colors.get(status, "#6b7280")


def get_status_icon(status: str) -> str:
    """Get icon for status."""
    icons = {
        "online": "✅",
        "slow": "⚠️",
        "very_slow": "🔴",
        "timeout": "⏱️",
        "offline": "❌",
        "error": "🔥"
    }
    return icons.get(status, "❓")


def render_api_health_dashboard_tab():
    """Main render function for API Health Dashboard."""

    # Hero section
    st.markdown("""
    <div style="
        text-align: center;
        margin: 2rem 0 3rem 0;
        padding: 3rem 2rem;
        background: linear-gradient(
            135deg,
            rgba(59, 130, 246, 0.05) 0%,
            rgba(139, 92, 246, 0.03) 50%,
            rgba(59, 130, 246, 0.05) 100%
        );
        border-radius: 24px;
        border: 1px solid rgba(59, 130, 246, 0.1);
        backdrop-filter: blur(20px);
    ">
        <h1 style="
            margin: 0 0 1rem 0;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.03em;
        ">
            API Health Dashboard
        </h1>
        <p style="
            margin: 0;
            font-size: 1.25rem;
            color: #cbd5e1;
            line-height: 1.6;
        ">
            Real-time monitoring of all external API endpoints used by TerraScout AI
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Check APIs button
    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        if st.button("🔄 Refresh Status", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Run health checks
    with st.spinner("🔍 Checking API health..."):
        results = check_all_apis()

    # Summary metrics
    st.markdown("### 📊 Summary")

    total = len(results)
    online = sum(1 for r in results if r["status"] == "online")
    slow = sum(1 for r in results if r["status"] in ["slow", "very_slow"])
    offline = sum(1 for r in results if r["status"] in ["offline", "timeout", "error"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total APIs",
            total,
            help="Total number of external APIs monitored"
        )

    with col2:
        st.metric(
            "Online",
            online,
            delta=f"{online/total*100:.0f}%",
            delta_color="normal"
        )

    with col3:
        st.metric(
            "Slow",
            slow,
            delta=f"{slow/total*100:.0f}%" if slow > 0 else "0%",
            delta_color="inverse"
        )

    with col4:
        st.metric(
            "Offline",
            offline,
            delta=f"{offline/total*100:.0f}%" if offline > 0 else "0%",
            delta_color="inverse"
        )

    st.markdown("---")

    # API Status by Category
    st.markdown("### 🗂️ API Status by Category")

    # Group by category
    from collections import defaultdict
    by_category = defaultdict(list)
    for result in results:
        by_category[result["category"]].append(result)

    # Display each category
    for category, apis in sorted(by_category.items()):
        with st.expander(f"📁 {category} ({len(apis)} APIs)", expanded=True):
            for api in sorted(apis, key=lambda x: x["name"]):
                status_color = get_status_color(api["status"])
                status_icon = get_status_icon(api["status"])

                col1, col2, col3, col4 = st.columns([3, 2, 2, 3])

                with col1:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.2rem;">{status_icon}</span>
                        <strong>{api['name']}</strong>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <span style="
                        background: {status_color}22;
                        color: {status_color};
                        padding: 0.25rem 0.75rem;
                        border-radius: 12px;
                        font-size: 0.875rem;
                        font-weight: 600;
                        border: 1px solid {status_color}44;
                    ">
                        {api['status'].upper()}
                    </span>
                    """, unsafe_allow_html=True)

                with col3:
                    if api['response_time_ms']:
                        st.markdown(f"⏱️ **{api['response_time_ms']:.0f}ms**")
                    else:
                        st.markdown("⏱️ **N/A**")

                with col4:
                    if api['error']:
                        st.markdown(f"⚠️ _{api['error'][:50]}_")
                    elif api['status_code']:
                        st.markdown(f"✅ _HTTP {api['status_code']}_")

    # Export API health data
    st.markdown("### 📥 Export API Health Data")

    if results:
        import pandas as pd

        export_data = []
        for api in results:
            export_data.append({
                "API": api["name"],
                "Status": api["status"],
                "Response_Time_ms": api.get("response_time_ms", 0),
                "Status_Code": api.get("status_code", "N/A"),
                "Category": api["category"],
                "Error": api.get("error", "")
            })

        df_health = pd.DataFrame(export_data)
        csv_health = df_health.to_csv(index=False)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download API Health Report (CSV)",
                csv_health,
                "api_health_report.csv",
                "text/csv",
                use_container_width=True
            )

    st.markdown("---")

    # Rate Limiter Stats
    st.markdown("### 🚦 Rate Limiter Statistics")
    if rate_limiter:
        display_rate_limit_dashboard()
    else:
        st.info("Rate limiter not initialized. Import rate_limiter to enable.")

    st.markdown("---")

    # Recommendations
    st.markdown("### 💡 Recommendations")

    if offline > 0:
        st.error(f"""
        **{offline} API(s) are offline or experiencing errors.**

        - Check your internet connection
        - Some APIs may be temporarily unavailable
        - Consider implementing fallback data sources
        """)

    if slow > 0:
        st.warning(f"""
        **{slow} API(s) are responding slowly (>1 second).**

        - Enable caching to reduce repeated requests
        - Consider implementing async requests for better performance
        - Some slow responses may be due to geographic distance
        """)

    if online == total:
        st.success("""
        **All APIs are operational! 🎉**

        - System is running at optimal performance
        - All data sources are available
        - Continue monitoring for any changes
        """)

    # Last updated
    st.markdown(f"""
    <div style="
        text-align: center;
        color: #94a3b8;
        font-size: 0.875rem;
        margin-top: 2rem;
        padding: 1rem;
        background: rgba(59, 130, 246, 0.05);
        border-radius: 8px;
    ">
        Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
        Auto-refresh: Every 5 minutes (cached)
    </div>
    """, unsafe_allow_html=True)
