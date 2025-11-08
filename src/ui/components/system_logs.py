"""
System Logs page - View system events and errors
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from loguru import logger

def render_system_logs():
    """Render system logs page."""
    st.title("📋 System Logs")
    st.markdown("View recent system events and errors")
    
    # Log level filter
    log_level = st.selectbox(
        "Log Level",
        ["All", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Filter logs by severity level"
    )
    
    # Number of lines
    num_lines = st.slider("Number of lines", 50, 500, 100)
    
    # Read log file
    try:
        log_file = Path("logs/spendsense.log")
        if not log_file.exists():
            st.warning("Log file not found. Logs will appear here once the system starts generating them.")
            return
        
        # Read last N lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines
        
        # Filter by log level
        if log_level != "All":
            filtered_lines = [
                line for line in recent_lines 
                if f" | {log_level}" in line or f"| {log_level} |" in line
            ]
        else:
            filtered_lines = recent_lines
        
        # Display logs
        st.text_area(
            "Recent Logs",
            value=''.join(filtered_lines),
            height=500,
            help="Most recent system logs"
        )
        
        # Download logs button
        st.download_button(
            "Download Full Logs",
            data=''.join(lines),
            file_name=f"spendsense_logs_{datetime.now().strftime('%Y%m%d')}.log",
            mime="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        st.error(f"Error reading logs: {str(e)}")

