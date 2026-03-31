"""
Advanced UI Components for TerraScout AI
Progressive feedback, status tracking, and user experience improvements
"""

import streamlit as st
import time
from contextlib import contextmanager
from typing import Optional, List, Callable
import traceback


@contextmanager
def progressive_spinner(steps: List[str], title: str = "Processing"):
    """
    Context manager for multi-step operations with progressive feedback.

    Usage:
        steps = ["Downloading tiles", "Running AI analysis", "Generating vectors"]
        with progressive_spinner(steps, "Analyzing Area") as update:
            update(0)  # Step 1: Downloading tiles
            # ... do work ...
            update(1)  # Step 2: Running AI analysis
            # ... do work ...
            update(2)  # Step 3: Generating vectors
    """
    total_steps = len(steps)
    progress_bar = st.progress(0.0, text=f"**{title}**")
    status_text = st.empty()

    def update_progress(step_index: int):
        """Update progress to a specific step."""
        if step_index < 0 or step_index >= total_steps:
            return

        progress = (step_index + 1) / total_steps
        current_step = steps[step_index]

        progress_bar.progress(progress, text=f"**{title}** ({step_index + 1}/{total_steps})")
        status_text.markdown(f"🔄 {current_step}...")

    try:
        yield update_progress
        # Success
        progress_bar.progress(1.0, text=f"**{title}** - Complete ✓")
        status_text.markdown("✅ **Operation completed successfully**")
        time.sleep(0.5)  # Brief pause to show completion
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        raise
    finally:
        # Cleanup after delay
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()


class ProgressiveStatus:
    """
    Advanced status tracker for complex multi-stage operations.

    Features:
    - Nested stages
    - Time tracking
    - Status persistence
    - Error capture

    Usage:
        status = ProgressiveStatus("Remote Structure Search")
        status.start_stage("Querying OSM", total_items=1000)
        for i in range(1000):
            status.update_progress(i + 1)
        status.complete_stage()
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = time.time()
        self.stages = []
        self.current_stage = None
        self._progress_bar = None
        self._status_text = None
        self._metrics_container = None

    def start_stage(self, stage_name: str, total_items: Optional[int] = None):
        """Start a new stage of the operation."""
        if self._progress_bar is None:
            self._progress_bar = st.progress(0.0)
            self._status_text = st.empty()
            self._metrics_container = st.container()

        self.current_stage = {
            "name": stage_name,
            "start_time": time.time(),
            "total_items": total_items,
            "processed_items": 0,
            "status": "running"
        }
        self.stages.append(self.current_stage)

        self._update_display()

    def update_progress(self, processed_items: int, message: Optional[str] = None):
        """Update progress within the current stage."""
        if not self.current_stage:
            return

        self.current_stage["processed_items"] = processed_items
        if message:
            self.current_stage["message"] = message

        self._update_display()

    def complete_stage(self, success: bool = True, message: Optional[str] = None):
        """Mark current stage as complete."""
        if not self.current_stage:
            return

        self.current_stage["status"] = "success" if success else "failed"
        self.current_stage["end_time"] = time.time()
        if message:
            self.current_stage["message"] = message

        self._update_display()
        self.current_stage = None

    def _update_display(self):
        """Update the UI display with current status."""
        if not self.current_stage:
            return

        stage = self.current_stage
        elapsed = time.time() - stage["start_time"]

        # Calculate progress
        if stage["total_items"]:
            progress = stage["processed_items"] / stage["total_items"]
            items_text = f"{stage['processed_items']:,} / {stage['total_items']:,}"
        else:
            progress = 0.0
            items_text = f"{stage['processed_items']:,} items"

        # Update progress bar
        self._progress_bar.progress(
            min(progress, 1.0),
            text=f"**{self.operation_name}** - {stage['name']}"
        )

        # Update status text
        message = stage.get("message", stage["name"])
        self._status_text.markdown(f"🔄 {message} ({items_text}, {elapsed:.1f}s)")

        # Update metrics
        with self._metrics_container:
            cols = st.columns(3)
            cols[0].metric("Stage", len(self.stages))
            cols[1].metric("Processed", f"{stage['processed_items']:,}")
            if stage["total_items"]:
                cols[2].metric("Progress", f"{progress * 100:.1f}%")

    def finalize(self, success: bool = True):
        """Clean up and show final status."""
        total_time = time.time() - self.start_time

        if self._progress_bar:
            self._progress_bar.progress(1.0 if success else 0.0)

        if self._status_text:
            if success:
                self._status_text.success(f"✅ {self.operation_name} completed in {total_time:.1f}s")
            else:
                self._status_text.error(f"❌ {self.operation_name} failed after {total_time:.1f}s")

        time.sleep(1)

        # Cleanup
        if self._progress_bar:
            self._progress_bar.empty()
        if self._status_text:
            self._status_text.empty()


def success_banner(message: str, icon: str = "✅"):
    """Display a success banner with modern styling and animation."""
    st.markdown(f"""
    <div class="success-banner" style="
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1.25rem 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        font-weight: 600;
        font-size: 1.05rem;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: slideInBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        backdrop-filter: blur(10px);
    ">
        <span style="
            font-size: 1.75rem;
            margin-right: 0.75rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
            display: inline-block;
            animation: iconPulse 2s infinite;
        ">{icon}</span>
        {message}
    </div>
    <style>
        @keyframes slideInBounce {{
            0% {{ transform: translateY(-20px); opacity: 0; }}
            60% {{ transform: translateY(5px); }}
            100% {{ transform: translateY(0); opacity: 1; }}
        }}
        @keyframes iconPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
    </style>
    """, unsafe_allow_html=True)


def warning_banner(message: str, icon: str = "⚠️"):
    """Display a warning banner with modern styling and animation."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1.25rem 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        font-weight: 600;
        font-size: 1.05rem;
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: slideInBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    ">
        <span style="
            font-size: 1.75rem;
            margin-right: 0.75rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
            display: inline-block;
            animation: shake 0.5s;
        ">{icon}</span>
        {message}
    </div>
    <style>
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            25% {{ transform: translateX(-5px); }}
            75% {{ transform: translateX(5px); }}
        }}
    </style>
    """, unsafe_allow_html=True)


def error_banner(message: str, details: Optional[str] = None, icon: str = "❌"):
    """Display an error banner with modern styling, animation, and optional details."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1.25rem 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        font-weight: 600;
        font-size: 1.05rem;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
        animation: slideInBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    ">
        <span style="
            font-size: 1.75rem;
            margin-right: 0.75rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
            display: inline-block;
            animation: shake 0.5s;
        ">{icon}</span>
        {message}
    </div>
    """, unsafe_allow_html=True)

    if details:
        with st.expander("🔍 Technical Details", expanded=False):
            st.code(details, language="python")


def info_card(title: str, content: str, icon: str = "ℹ️", color: str = "#06b6d4"):
    """Display an informational card with modern glass-morphism styling."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}33 0%, {color}11 100%);
        border-left: 5px solid {color};
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    ">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem;">
            <span style="
                font-size: 2rem;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            ">{icon}</span>
            <strong style="
                font-size: 1.25rem;
                color: {color};
                font-weight: 700;
                letter-spacing: 0.5px;
            ">{title}</strong>
        </div>
        <div style="
            color: #e5e7eb;
            line-height: 1.8;
            font-size: 1rem;
            padding-left: 3rem;
        ">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: Optional[str] = None, icon: str = "📊"):
    """Display a modern metric card with gradient, glow effect, and optional delta."""
    delta_html = ""
    if delta:
        delta_color = "#10b981" if not delta.startswith("-") else "#ef4444"
        delta_icon = "↗" if not delta.startswith("-") else "↘"
        delta_html = f'''
        <div style="
            color: {delta_color};
            font-size: 0.95rem;
            margin-top: 0.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        ">
            <span style="font-size: 1.1rem;">{delta_icon}</span>
            {delta}
        </div>
        '''

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 1.75rem;
        border-radius: 16px;
        margin: 1rem 0;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 20px rgba(6, 182, 212, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.1) 0%, transparent 70%);
            pointer-events: none;
        "></div>
        <div style="position: relative; z-index: 1;">
            <div style="
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 0.75rem;
            ">
                <span style="
                    font-size: 1.5rem;
                    filter: drop-shadow(0 2px 8px rgba(6, 182, 212, 0.5));
                ">{icon}</span>
                <div style="
                    color: #94a3b8;
                    font-size: 0.95rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    font-weight: 600;
                ">
                    {label}
                </div>
            </div>
            <div style="
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: -1px;
            ">
                {value}
            </div>
            {delta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def loading_dots(text: str = "Loading"):
    """Display animated loading dots."""
    placeholder = st.empty()

    for i in range(3):
        dots = "." * (i + 1)
        placeholder.markdown(f"**{text}{dots}**")
        time.sleep(0.3)

    placeholder.empty()


@contextmanager
def timed_operation(operation_name: str, show_spinner: bool = True):
    """
    Context manager to time an operation and display results.

    Usage:
        with timed_operation("Downloading tiles"):
            # ... your code ...
            pass
    """
    start_time = time.time()
    spinner_placeholder = st.empty()

    if show_spinner:
        with spinner_placeholder:
            st.spinner(f"⏳ {operation_name}...")

    try:
        yield
        elapsed = time.time() - start_time
        spinner_placeholder.empty()
        success_banner(f"{operation_name} completed in {elapsed:.2f}s", "✅")
    except Exception as e:
        elapsed = time.time() - start_time
        spinner_placeholder.empty()
        error_banner(
            f"{operation_name} failed after {elapsed:.2f}s",
            details=traceback.format_exc()
        )
        raise


def confirmation_dialog(message: str, confirm_text: str = "Confirm", cancel_text: str = "Cancel") -> bool:
    """
    Display a confirmation dialog and return user choice.

    Note: This is a simplified version. For production, use a modal library.
    """
    st.warning(f"⚠️ {message}")

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button(confirm_text, type="primary", key=f"confirm_{hash(message)}"):
            return True

    with col2:
        if st.button(cancel_text, key=f"cancel_{hash(message)}"):
            return False

    return False


def section_header(title: str, subtitle: Optional[str] = None, icon: str = "🔹"):
    """Display a modern section header with optional subtitle."""
    subtitle_html = ""
    if subtitle:
        subtitle_html = f'''
        <div style="
            color: #94a3b8;
            font-size: 1rem;
            margin-top: 0.5rem;
            font-weight: 400;
        ">
            {subtitle}
        </div>
        '''

    st.markdown(f"""
    <div style="
        margin: 2rem 0 1.5rem 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid #334155;
        animation: fadeInDown 0.5s ease-out;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 1rem;
        ">
            <span style="
                font-size: 2.5rem;
                filter: drop-shadow(0 4px 8px rgba(6, 182, 212, 0.3));
            ">{icon}</span>
            <div>
                <h2 style="
                    margin: 0;
                    font-size: 2rem;
                    font-weight: 800;
                    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    letter-spacing: -0.5px;
                ">
                    {title}
                </h2>
                {subtitle_html}
            </div>
        </div>
    </div>
    <style>
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
    """, unsafe_allow_html=True)


def glassmorphism_container(content_html: str, padding: str = "2rem"):
    """Display content in a modern glassmorphism container."""
    st.markdown(f"""
    <div style="
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: {padding};
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    ">
        {content_html}
    </div>
    """, unsafe_allow_html=True)


def stats_grid(stats: List[dict], columns: int = 3):
    """
    Display a grid of statistics cards.

    Args:
        stats: List of dicts with keys: label, value, icon, color (optional)
        columns: Number of columns in the grid
    """
    cols = st.columns(columns)

    for i, stat in enumerate(stats):
        col_idx = i % columns
        label = stat.get("label", "")
        value = stat.get("value", "")
        icon = stat.get("icon", "📊")
        color = stat.get("color", "#06b6d4")

        with cols[col_idx]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
                border: 1px solid {color}44;
                padding: 1.5rem;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                margin-bottom: 1rem;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">
                    {icon}
                </div>
                <div style="
                    color: #94a3b8;
                    font-size: 0.85rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    margin-bottom: 0.5rem;
                ">
                    {label}
                </div>
                <div style="
                    font-size: 1.75rem;
                    font-weight: 700;
                    color: {color};
                ">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)


def enhanced_progress_bar(progress: float, label: str = "", color: str = "#06b6d4"):
    """Display an enhanced progress bar with gradient and glow."""
    percentage = int(progress * 100)

    st.markdown(f"""
    <div style="margin: 1.5rem 0;">
        {f'<div style="color: #e5e7eb; margin-bottom: 0.5rem; font-weight: 600;">{label}</div>' if label else ''}
        <div style="
            background: #1e293b;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            border: 1px solid #334155;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {color} 0%, {color}dd 100%);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                color: white;
                font-size: 0.85rem;
                box-shadow: 0 0 20px {color}88;
                transition: width 0.3s ease;
                animation: shimmer 2s infinite;
            ">
                {percentage}%
            </div>
        </div>
    </div>
    <style>
        @keyframes shimmer {{
            0% {{ box-shadow: 0 0 20px {color}66; }}
            50% {{ box-shadow: 0 0 30px {color}aa; }}
            100% {{ box-shadow: 0 0 20px {color}66; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def category_header(title: str, count: int, icon: str = "🗂️"):
    """Display a styled category header with icon and count badge."""
    st.markdown(f"""
    <div style="
        margin: 2rem 0 1rem 0; padding: 0.75rem 1.25rem;
        background: rgba(14, 165, 233, 0.06);
        border-left: 3px solid #0ea5e9; border-radius: 8px;
        backdrop-filter: blur(8px);
    ">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.4rem; filter: drop-shadow(0 2px 8px rgba(14, 165, 233, 0.4));">{icon}</span>
            <h3 style="margin: 0; font-size: 1.25rem; font-weight: 600; color: #fafafa; letter-spacing: -0.02em;">{title}</h3>
            <span style="
                background: rgba(14, 165, 233, 0.15); color: #38bdf8;
                padding: 0.2rem 0.6rem; border-radius: 10px;
                font-size: 0.8rem; font-weight: 600;
                border: 1px solid rgba(14, 165, 233, 0.25);
            ">{count}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def hero_section(title: str, subtitle: str, features: List[str] = None):
    """Display a hero section banner with gradient background."""
    features_html = ""
    if features:
        features_items = " ".join([
            f'<span style="color: #38bdf8; margin: 0 0.75rem;">&#9632;</span>{feat}'
            for feat in features
        ])
        features_html = f"""
        <div style="
            margin-top: 1.5rem; font-size: 0.9375rem; color: #cbd5e1;
            display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem;
        ">{features_items}</div>
        """

    st.markdown(f"""
    <div style="
        text-align: center; margin: 1.5rem 0 2.5rem 0; padding: 2.5rem 2rem;
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.05) 0%, rgba(139, 92, 246, 0.03) 50%, rgba(14, 165, 233, 0.05) 100%);
        border-radius: 20px; border: 1px solid rgba(14, 165, 233, 0.1);
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    ">
        <h1 style="
            margin: 0 0 1rem 0; font-size: 2.5rem; font-weight: 700;
            background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; letter-spacing: -0.03em;
        ">{title}</h1>
        <p style="margin: 0; font-size: 1.125rem; color: #cbd5e1; line-height: 1.6; max-width: 800px; margin: 0 auto;">{subtitle}</p>
        {features_html}
    </div>
    """, unsafe_allow_html=True)
