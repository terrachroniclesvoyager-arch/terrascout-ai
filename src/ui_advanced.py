"""
Advanced UI Components for TerraScout AI
Beautiful, reusable components with animations and interactivity
"""

import streamlit as st
from typing import List, Dict, Optional


def metric_card(label: str, value: str, icon: str = "📊", color: str = "#3b82f6",
                change: Optional[str] = None, subtitle: Optional[str] = None):
    """
    Beautiful metric card with optional change indicator.

    Args:
        label: Metric label
        value: Main value to display
        icon: Emoji icon
        color: Accent color
        change: Optional change value (e.g., "+5.2%")
        subtitle: Optional subtitle text
    """

    change_html = ""
    if change:
        change_color = "#10b981" if change.startswith("+") else "#ef4444"
        change_html = f"""
        <div style="
            color: {change_color};
            font-size: 0.875rem;
            font-weight: 600;
            margin-top: 0.25rem;
        ">
            {change}
        </div>
        """

    subtitle_html = ""
    if subtitle:
        subtitle_html = f"""
        <div style="
            color: #94a3b8;
            font-size: 0.75rem;
            margin-top: 0.25rem;
        ">
            {subtitle}
        </div>
        """

    st.markdown(f"""
    <div class="stats-card animate-fadeIn">
        <div style="display: flex; align-items: flex-start; gap: 1rem;">
            <div style="
                font-size: 2rem;
                line-height: 1;
            ">
                {icon}
            </div>
            <div style="flex: 1;">
                <div style="
                    color: #94a3b8;
                    font-size: 0.875rem;
                    font-weight: 500;
                    margin-bottom: 0.5rem;
                ">
                    {label}
                </div>
                <div style="
                    color: {color};
                    font-size: 1.5rem;
                    font-weight: 700;
                    line-height: 1;
                ">
                    {value}
                </div>
                {change_html}
                {subtitle_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def progress_ring(percentage: float, label: str, color: str = "#3b82f6", size: int = 120):
    """
    Circular progress indicator.

    Args:
        percentage: Progress value (0-100)
        label: Label text
        color: Ring color
        size: Size in pixels
    """

    circumference = 2 * 3.14159 * 45  # radius = 45
    offset = circumference - (percentage / 100 * circumference)

    st.markdown(f"""
    <div style="text-align: center;">
        <svg width="{size}" height="{size}" style="transform: rotate(-90deg);">
            <!-- Background circle -->
            <circle
                cx="{size/2}"
                cy="{size/2}"
                r="45"
                fill="none"
                stroke="rgba(255,255,255,0.1)"
                stroke-width="8"
            />
            <!-- Progress circle -->
            <circle
                cx="{size/2}"
                cy="{size/2}"
                r="45"
                fill="none"
                stroke="{color}"
                stroke-width="8"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{offset}"
                stroke-linecap="round"
                style="transition: stroke-dashoffset 0.5s ease;"
            />
        </svg>
        <div style="
            margin-top: -60px;
            font-size: 1.5rem;
            font-weight: 700;
            color: {color};
        ">
            {percentage:.0f}%
        </div>
        <div style="
            color: #94a3b8;
            font-size: 0.875rem;
            margin-top: 1rem;
        ">
            {label}
        </div>
    </div>
    """, unsafe_allow_html=True)


def data_table_enhanced(data: List[Dict], max_rows: int = 10):
    """
    Enhanced data table with styling.

    Args:
        data: List of dictionaries
        max_rows: Maximum rows to display
    """

    if not data:
        st.info("No data available")
        return

    import pandas as pd

    df = pd.DataFrame(data[:max_rows])

    # Style the dataframe
    st.markdown("""
    <style>
    .dataframe {
        background: rgba(10, 15, 30, 0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 12px !important;
    }
    .dataframe th {
        background: rgba(59, 130, 246, 0.1) !important;
        color: #3b82f6 !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    .dataframe td {
        color: #cbd5e1 !important;
        padding: 10px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.dataframe(df, use_container_width=True, hide_index=True)


def alert_box(message: str, type: str = "info", icon: str = None):
    """
    Styled alert box.

    Args:
        message: Alert message
        type: "info", "success", "warning", "error"
        icon: Optional custom icon
    """

    colors = {
        "info": {"bg": "rgba(59, 130, 246, 0.1)", "border": "#3b82f6", "icon": "ℹ️"},
        "success": {"bg": "rgba(16, 185, 129, 0.1)", "border": "#10b981", "icon": "✅"},
        "warning": {"bg": "rgba(245, 158, 11, 0.1)", "border": "#f59e0b", "icon": "⚠️"},
        "error": {"bg": "rgba(239, 68, 68, 0.1)", "border": "#ef4444", "icon": "❌"}
    }

    config = colors.get(type, colors["info"])
    alert_icon = icon or config["icon"]

    st.markdown(f"""
    <div style="
        background: {config['bg']};
        border-left: 4px solid {config['border']};
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <div style="font-size: 1.5rem;">{alert_icon}</div>
        <div style="color: #cbd5e1;">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def loading_spinner(text: str = "Loading..."):
    """
    Animated loading spinner.

    Args:
        text: Loading text
    """

    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <div class="animate-spin" style="
            width: 40px;
            height: 40px;
            border: 4px solid rgba(59, 130, 246, 0.2);
            border-top-color: #3b82f6;
            border-radius: 50%;
            margin: 0 auto 1rem auto;
        "></div>
        <div style="color: #94a3b8;">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def timeline_item(time: str, title: str, description: str, icon: str = "📍"):
    """
    Timeline item component.

    Args:
        time: Time/date string
        title: Event title
        description: Event description
        icon: Icon emoji
    """

    st.markdown(f"""
    <div style="
        display: flex;
        gap: 1rem;
        padding: 1rem;
        border-left: 2px solid rgba(59, 130, 246, 0.3);
        margin-left: 1rem;
    ">
        <div style="
            width: 40px;
            height: 40px;
            background: rgba(59, 130, 246, 0.2);
            border: 2px solid #3b82f6;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
            margin-left: -21px;
        ">
            {icon}
        </div>
        <div style="flex: 1;">
            <div style="
                color: #94a3b8;
                font-size: 0.75rem;
                margin-bottom: 0.25rem;
            ">
                {time}
            </div>
            <div style="
                color: #e8ecf4;
                font-weight: 600;
                margin-bottom: 0.25rem;
            ">
                {title}
            </div>
            <div style="color: #94a3b8; font-size: 0.875rem;">
                {description}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def feature_grid(features: List[Dict]):
    """
    Grid of feature cards.

    Args:
        features: List of dicts with keys: icon, title, description
    """

    cols = st.columns(min(len(features), 3))

    for i, feature in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="stats-card hover-scale" style="text-align: center; height: 100%;">
                <div style="font-size: 2.5rem; margin-bottom: 1rem;">
                    {feature.get('icon', '⭐')}
                </div>
                <div style="
                    color: #e8ecf4;
                    font-weight: 600;
                    font-size: 1.1rem;
                    margin-bottom: 0.5rem;
                ">
                    {feature.get('title', 'Feature')}
                </div>
                <div style="color: #94a3b8; font-size: 0.875rem;">
                    {feature.get('description', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)


def mini_chart(values: List[float], color: str = "#3b82f6", height: int = 60):
    """
    Mini sparkline chart.

    Args:
        values: List of numeric values
        color: Line color
        height: Chart height in pixels
    """

    if not values or len(values) < 2:
        return

    # Normalize values to 0-1 range
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val if max_val != min_val else 1

    normalized = [(v - min_val) / range_val for v in values]

    # Create SVG path
    width = 200
    points = []
    for i, val in enumerate(normalized):
        x = (i / (len(values) - 1)) * width
        y = height - (val * (height - 10))
        points.append(f"{x},{y}")

    path = " L ".join(points)

    st.markdown(f"""
    <svg width="{width}" height="{height}" style="display: block;">
        <path
            d="M {path}"
            fill="none"
            stroke="{color}"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
        />
    </svg>
    """, unsafe_allow_html=True)


# Usage examples in docstring
"""
USAGE EXAMPLES:

1. Metric Card:
```python
from src.ui_advanced import metric_card

metric_card(
    label="Temperature",
    value="24°C",
    icon="🌡️",
    color="#ef4444",
    change="+2.5°C",
    subtitle="New York, USA"
)
```

2. Progress Ring:
```python
from src.ui_advanced import progress_ring

progress_ring(
    percentage=75,
    label="API Health",
    color="#10b981"
)
```

3. Alert Box:
```python
from src.ui_advanced import alert_box

alert_box(
    "All systems operational!",
    type="success"
)
```

4. Feature Grid:
```python
from src.ui_advanced import feature_grid

features = [
    {"icon": "🌍", "title": "Global Coverage", "description": "Worldwide data"},
    {"icon": "⚡", "title": "Real-Time", "description": "Live updates"},
    {"icon": "📊", "title": "Analytics", "description": "Deep insights"}
]

feature_grid(features)
```
"""
