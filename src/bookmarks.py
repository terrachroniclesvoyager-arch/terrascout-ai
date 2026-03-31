"""
Bookmarks manager for TerraScout AI.
Save, load and manage favorite locations in a JSON file.
"""

import json
import os
from datetime import datetime
import streamlit as st
from src.location_context import set_location

BOOKMARKS_FILE = "output/bookmarks.json"


def _load_bookmarks():
    """Load bookmarks from JSON file."""
    try:
        if os.path.exists(BOOKMARKS_FILE):
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_bookmarks(bookmarks):
    """Save bookmarks to JSON file."""
    os.makedirs(os.path.dirname(BOOKMARKS_FILE), exist_ok=True)
    with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
        json.dump(bookmarks, f, indent=2, ensure_ascii=False)


def render_bookmarks_sidebar():
    """Render bookmarks section in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 Bookmarks")
    
    bookmarks = _load_bookmarks()
    
    # Add new bookmark form
    with st.sidebar.expander("Add Bookmark", expanded=False):
        bk_name = st.text_input("Name", key="bk_name", placeholder="e.g. My Cabin")
        col1, col2 = st.columns(2)
        with col1:
            bk_lat = st.number_input("Latitude", -90.0, 90.0, 41.9, step=0.01, key="bk_lat", format="%.4f")
        with col2:
            bk_lon = st.number_input("Longitude", -180.0, 180.0, 12.5, step=0.01, key="bk_lon", format="%.4f")
        bk_notes = st.text_input("Notes (optional)", key="bk_notes", placeholder="e.g. Good fishing spot")
        
        if st.button("Save Bookmark", key="bk_save", use_container_width=True):
            if bk_name.strip():
                new_bk = {
                    "name": bk_name.strip(),
                    "lat": bk_lat,
                    "lon": bk_lon,
                    "notes": bk_notes.strip(),
                    "created": datetime.now().isoformat(),
                }
                bookmarks.append(new_bk)
                _save_bookmarks(bookmarks)
                st.success(f"Saved: {bk_name}")
                st.rerun()
            else:
                st.warning("Enter a name for the bookmark.")
    
    # List existing bookmarks
    if not bookmarks:
        st.sidebar.caption("No bookmarks yet. Add one above!")
        return
    
    # Search filter
    search = st.sidebar.text_input("🔍 Filter", key="bk_search", placeholder="Search bookmarks...")
    
    filtered = bookmarks
    if search:
        search_lower = search.lower()
        filtered = [b for b in bookmarks if search_lower in b["name"].lower() or search_lower in b.get("notes", "").lower()]
    
    for i, bk in enumerate(filtered):
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            label = f"**{bk['name']}** ({bk['lat']:.2f}, {bk['lon']:.2f})"
            if st.button(label, key=f"bk_go_{i}", use_container_width=True):
                set_location(bk["lat"], bk["lon"], source="bookmark")
                st.session_state.current_page = "command_center"
                st.toast(f"Navigated to {bk['name']}")
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"bk_del_{i}"):
                # Find by unique timestamp to avoid wrong-index with duplicates
                for orig_idx, orig_bk in enumerate(bookmarks):
                    if orig_bk.get("created") == bk.get("created") and orig_bk.get("name") == bk.get("name"):
                        bookmarks.pop(orig_idx)
                        break
                _save_bookmarks(bookmarks)
                st.rerun()
    
    st.sidebar.caption(f"{len(filtered)}/{len(bookmarks)} bookmarks shown")
