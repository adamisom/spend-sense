"""
SpendSense Operator Dashboard - Main Entry Point
Provides comprehensive view of system operations and user analytics
"""
import streamlit as st
import os

# CRITICAL: set_page_config() must be the FIRST Streamlit command
# Must come before any other Streamlit commands or imports that use Streamlit
st.set_page_config(
    page_title="SpendSense Operator Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Basic Authentication (plain text password for simplicity)
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        password = os.getenv("STREAMLIT_PASSWORD")
        
        if password:
            st.session_state["password_correct"] = st.session_state["password"] == password
        else:
            # No password set - allow access (for local dev)
            st.session_state["password_correct"] = True
    
    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.text_input("Enter password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        st.stop()
    else:
        # Password correct
        return True

# Check authentication (skip in local dev if no password set)
if os.getenv("STREAMLIT_PASSWORD"):
    check_password()

# Now safe to import other modules
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from src.ui.components.user_analytics import render_user_analytics
from src.ui.components.user_view import render_user_view
from src.ui.components.recommendation_engine import render_recommendation_engine
from src.ui.components.data_quality import render_data_quality
from src.ui.components.performance_metrics import render_performance_metrics
from src.ui.components.system_logs import render_system_logs
from loguru import logger

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.success-metric {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
}

.warning-metric {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
}

.error-metric {
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
}

.sidebar-info {
    background-color: #e7f3ff;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'db_path' not in st.session_state:
        # Use environment variable if set, otherwise default
        st.session_state.db_path = os.getenv("DATABASE_PATH", "db/spend_sense.db")
    
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    
    # Removed auto_refresh - not implemented and Streamlit doesn't support it well

def get_system_health() -> dict:
    """Get basic system health metrics."""
    try:
        with database_transaction(st.session_state.db_path) as conn:
            # User counts
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            users_with_signals = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_signals").fetchone()[0]
            users_with_recommendations = conn.execute("""
                SELECT COUNT(DISTINCT user_id) FROM recommendations 
                WHERE created_at >= datetime('now', '-7 days')
            """).fetchone()[0]
            
            # Data quality metrics
            avg_data_quality_result = conn.execute("""
                SELECT AVG(CAST(JSON_EXTRACT(signals, '$.data_quality_score') AS FLOAT))
                FROM user_signals 
                WHERE window = '180d'
            """).fetchone()[0]
            avg_data_quality = avg_data_quality_result if avg_data_quality_result is not None else 0.0
            
            # Diagnostic: Check if transactions exist
            transaction_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            
            # Recent activity
            recent_recommendations = conn.execute("""
                SELECT COUNT(*) FROM recommendations 
                WHERE created_at >= datetime('now', '-24 hours')
            """).fetchone()[0]
            
            # Determine health status based on multiple criteria
            health_checks = {
                'has_users': total_users > 0,
                'has_transactions': transaction_count > 0,
                'has_signals': users_with_signals > 0,
                'has_data_quality': avg_data_quality > 0.0,
                'has_recent_activity': recent_recommendations > 0 or users_with_recommendations > 0
            }
            
            # System is healthy if core components are working
            is_healthy = (
                health_checks['has_users'] and
                health_checks['has_transactions'] and
                health_checks['has_signals'] and
                health_checks['has_data_quality']
            )
            
            return {
                'total_users': total_users,
                'users_with_signals': users_with_signals,
                'users_with_recommendations': users_with_recommendations,
                'signal_coverage': users_with_signals / max(total_users, 1) * 100,
                'avg_data_quality': avg_data_quality,
                'recent_recommendations': recent_recommendations,
                'transaction_count': transaction_count,
                'system_status': 'healthy' if is_healthy else 'error',
                'health_checks': health_checks
            }
            
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            'total_users': 0,
            'users_with_signals': 0,
            'users_with_recommendations': 0,
            'signal_coverage': 0.0,
            'avg_data_quality': 0.0,
            'recent_recommendations': 0,
            'transaction_count': 0,
            'system_status': 'error',
            'health_checks': {
                'has_users': False,
                'has_transactions': False,
                'has_signals': False,
                'has_data_quality': False,
                'has_recent_activity': False
            }
        }

def render_sidebar():
    """Render sidebar with navigation and controls."""
    st.sidebar.title("🎯 SpendSense Operator")
    st.sidebar.markdown("---")
    
    # Navigation
    st.sidebar.subheader("📊 Navigation")
    page = st.sidebar.selectbox(
        "Select View",
        ["User View", "System Overview", "User Analytics", "Recommendation Engine", 
         "Data Quality", "Performance Metrics", "System Logs"]
    )
    
    st.sidebar.markdown("---")
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data", help="Reload all data from the database. Use this after running scripts or when data seems stale."):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    # Quick Actions
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Quick Actions")
    
    if st.sidebar.button("🔧 Compute Signals", help="Compute signals for all users (may take 1-2 minutes). After completion, user personas will appear and you can view personalized recommendations."):
        st.session_state.compute_signals = True
        st.rerun()
    
    # System health in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏥 System Health")
    
    health = get_system_health()
    health_checks = health.get('health_checks', {})
    
    # Show health status with visible criteria
    if health['system_status'] == 'healthy':
        st.sidebar.success("✅ System Healthy")
        # Show criteria in a compact info box
        checks = health_checks
        criteria_list = []
        if checks.get('has_users'):
            criteria_list.append("Users loaded")
        if checks.get('has_transactions'):
            criteria_list.append("Transactions available")
        if checks.get('has_signals'):
            criteria_list.append("Signals computed")
        if checks.get('has_data_quality'):
            criteria_list.append("Data quality > 0")
        
        if criteria_list:
            st.sidebar.caption("**Why healthy:** " + " • ".join(criteria_list))
        
        if checks.get('has_recent_activity'):
            st.sidebar.caption("✅ Recent activity detected")
        else:
            st.sidebar.caption("ℹ️ No recent recommendations (normal)")
    else:
        st.sidebar.error("❌ System Issues")
        # Show missing components
        checks = health_checks
        issues = []
        if not checks.get('has_users'):
            issues.append("No users")
            st.sidebar.info("💡 Run: `python -m src.ingest.data_generator --users 50`")
        if not checks.get('has_transactions'):
            issues.append("No transactions")
            st.sidebar.info("💡 Run: `python scripts/load_data.py`")
        if not checks.get('has_signals'):
            issues.append("No signals")
            st.sidebar.info("💡 Click '🔧 Compute Signals' above")
        if not checks.get('has_data_quality'):
            issues.append("Data quality = 0")
            st.sidebar.info("💡 Check transactions and recompute signals")
        
        if issues:
            st.sidebar.caption("**Issues:** " + " • ".join(issues))
    
    st.sidebar.markdown(f"""
    <div class="sidebar-info">
    <strong>Quick Stats:</strong><br>
    👥 Users: {health['total_users']}<br>
    📊 Signal Coverage: {health['signal_coverage']:.1f}%<br>
    🎯 Avg Data Quality: {health['avg_data_quality']:.2f}<br>
    📝 Recent Recs: {health['recent_recommendations']}<br>
    💳 Transactions: {health.get('transaction_count', 0):,}
    </div>
    """, unsafe_allow_html=True)
    
    # Last refresh info
    if st.session_state.last_refresh:
        st.sidebar.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    return page

def render_system_overview():
    """Render system overview page."""
    st.title("📊 System Overview")
    st.markdown("High-level system health and key metrics")
    
    # Get system metrics
    health = get_system_health()
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Users",
            value=f"{health['total_users']:,}",
            help="Total number of users in the system"
        )
    
    with col2:
        st.metric(
            label="Signal Coverage",
            value=f"{health['signal_coverage']:.1f}%",
            delta=None,
            help="Percentage of users with computed signals"
        )
    
    with col3:
        st.metric(
            label="Avg Data Quality",
            value=f"{health['avg_data_quality']:.2f}",
            delta=None,
            help="Average data quality score (0.0-1.0)"
        )
    
    with col4:
        st.metric(
            label="24h Recommendations",
            value=f"{health['recent_recommendations']:,}",
            help="Recommendations generated in last 24 hours"
        )
    
    st.markdown("---")
    
    # System status cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Recommendation Engine")
        if health['users_with_recommendations'] > 0:
            st.success(f"✅ Active - serving {health['users_with_recommendations']} users")
        else:
            st.error("❌ No recent recommendations generated")
    
    with col2:
        st.subheader("📊 Signal Detection") 
        if health['users_with_signals'] > 0:
            st.success(f"✅ Active - {health['users_with_signals']} users processed")
        else:
            st.error("❌ No user signals found")
            st.info("💡 Click '🔧 Compute Signals' in the sidebar to generate signals for all users")

def compute_signals_from_dashboard(db_path: str = "db/spend_sense.db"):
    """Compute signals for all users from dashboard."""
    try:
        import subprocess
        import sys
        
        # Get project root (parent of src/)
        project_root = Path(__file__).parent.parent.parent
        script_path = project_root / "scripts" / "compute_signals.py"
        
        # Set environment with PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        # Run signal computation script
        result = subprocess.run(
            [sys.executable, str(script_path), "--db-path", db_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(project_root),  # Set working directory
            env=env  # Pass environment with PYTHONPATH
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Signal computation timed out after 5 minutes"
    except Exception as e:
        return False, f"Error running script: {str(e)}"

def main():
    """Main dashboard application."""
    # Initialize session state
    initialize_session_state()
    
    # Handle signal computation request
    if st.session_state.get('compute_signals', False):
        st.session_state.compute_signals = False  # Reset flag
        
        # Show clear status at top of page
        st.info("🔄 Computing signals for all users... This may take 1-2 minutes. Please wait.")
        
        with st.spinner("⏳ Processing... This may take a few minutes."):
            success, message = compute_signals_from_dashboard(st.session_state.db_path)
        
        # Clear the info message
        st.empty()
        
        if success:
            # Extract user count from message if available
            import re
            user_match = re.search(r'(\d+)\s*users?', message, re.IGNORECASE)
            user_count = user_match.group(1) if user_match else "all"
            
            # Check if signals actually have data quality > 0
            with database_transaction(st.session_state.db_path) as conn:
                sample_result = conn.execute("""
                    SELECT signals FROM user_signals 
                    WHERE window = '180d' 
                    LIMIT 1
                """).fetchone()
                
                if sample_result:
                    import json
                    sample_signals = json.loads(sample_result['signals'])
                    sample_quality = sample_signals.get('data_quality_score', 0.0)
                    
                    if sample_quality == 0.0:
                        st.warning("⚠️ **Signals computed but data quality is 0.0**")
                        st.info(f"""
                        **Diagnosis:**
                        - Signals were saved to database
                        - But data_quality_score = 0.0 for all users
                        - This usually means transactions are empty or computation failed
                        
                        **Check:**
                        - Are there transactions in the database?
                        - Check Railway logs for computation errors
                        - Sample signal keys: {list(sample_signals.keys())[:5]}
                        """)
                    else:
                        st.success(f"✅ **Signal computation complete for {user_count} users!**")
                        st.info("""
                        **What happened:**
                        - Behavioral signals have been computed for all users
                        - User personas should now appear (colored icons instead of gray in User View)
                        
                        **Next steps:**
                        1. The page will refresh automatically in a moment
                        2. Go to "User View" and click a user ID to see their persona
                        3. Recommendations will be auto-generated (or run `python scripts/generate_recommendations.py --all`)
                        """)
                else:
                    st.error("❌ **No signals found in database after computation**")
                    st.info("Check Railway logs for errors")
            
            st.session_state.last_refresh = datetime.now()
            import time
            time.sleep(3)  # Give user time to read the message
            st.rerun()
        else:
            st.error(f"❌ **Signal computation failed**")
            st.error(f"Error: {message}")
            st.code(message[:500] if len(message) > 500 else message)  # Show error details
            st.info("💡 You can also run: `python scripts/compute_signals.py` from the command line")
    
    # Note: Auto-refresh removed - Streamlit doesn't support true auto-refresh well
    # Users can click "🔄 Refresh Data" button in sidebar to manually refresh
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Route to selected page
    if selected_page == "User View":
        render_user_view()
    elif selected_page == "System Overview":
        render_system_overview()
    elif selected_page == "User Analytics":
        render_user_analytics()
    elif selected_page == "Recommendation Engine":
        render_recommendation_engine()
    elif selected_page == "Data Quality":
        render_data_quality()
    elif selected_page == "Performance Metrics":
        render_performance_metrics()
    elif selected_page == "System Logs":
        render_system_logs()
    
    # Footer
    st.markdown("---")
    st.markdown("*SpendSense Operator Dashboard v1.0*")

if __name__ == "__main__":
    main()

