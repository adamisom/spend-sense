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
    
    # Read log file or generate mock logs
    try:
        log_file = Path("logs/spendsense.log")
        if not log_file.exists():
            # Generate mock logs for demonstration
            mock_logs = generate_mock_logs()
            filtered_lines = filter_mock_logs(mock_logs, log_level)
            
            st.info("💡 **Demo Mode**: Showing mock system logs. In production, logs will be read from `logs/spendsense.log`")
            st.markdown("---")
            
            # Display logs
            st.text_area(
                "Recent Logs",
                value=''.join(filtered_lines),
                height=500,
                help="Most recent system logs"
            )
            
            # Download mock logs button
            st.download_button(
                "Download Mock Logs",
                data=''.join(mock_logs),
                file_name=f"spendsense_logs_{datetime.now().strftime('%Y%m%d')}.log",
                mime="text/plain"
            )
            return
        
        # Read actual log file
        
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

def generate_mock_logs() -> list:
    """Generate realistic mock system logs for demonstration."""
    from datetime import datetime, timedelta
    import random
    
    logs = []
    base_time = datetime.now() - timedelta(hours=2)
    
    # Log format: 2025-01-10 14:23:45.123 | INFO | module:function:line - message
    
    log_events = [
        # System startup
        (base_time + timedelta(minutes=1), "INFO", "src.db.connection:initialize_db:166", "Database initialized successfully: db/spend_sense.db"),
        (base_time + timedelta(minutes=2), "INFO", "src.ingest.data_generator:generate:935", "Generating synthetic data for 30 users (seed: 42)"),
        (base_time + timedelta(minutes=3), "INFO", "src.ingest.data_generator:save_to_csv:252", "Saved 30 records to data/synthetic/users.csv"),
        (base_time + timedelta(minutes=3), "INFO", "src.ingest.data_generator:save_to_csv:252", "Saved 45 records to data/synthetic/accounts.csv"),
        (base_time + timedelta(minutes=4), "INFO", "src.ingest.data_generator:save_to_csv:252", "Saved 14218 records to data/synthetic/transactions.csv"),
        
        # Signal computation
        (base_time + timedelta(minutes=5), "INFO", "scripts.compute_signals:main:45", "Computing signals for 30 users (window: 180d)"),
        (base_time + timedelta(minutes=6), "INFO", "src.features.credit:compute_credit_signals:89", "✅ Saved signals for user_001 (quality: 0.95)"),
        (base_time + timedelta(minutes=6), "INFO", "src.features.credit:compute_credit_signals:89", "✅ Saved signals for user_002 (quality: 0.87)"),
        (base_time + timedelta(minutes=7), "WARNING", "src.features.income:compute_income_signals:124", "⚠️ Low transaction count for user_015 (12 transactions, minimum: 20)"),
        (base_time + timedelta(minutes=7), "INFO", "src.features.income:compute_income_signals:89", "✅ Saved signals for user_015 (quality: 0.42)"),
        (base_time + timedelta(minutes=8), "INFO", "scripts.compute_signals:main:52", "✅ Signal computation complete: 30 users processed"),
        
        # Persona assignment
        (base_time + timedelta(minutes=9), "INFO", "src.personas.persona_classifier:assign_persona:156", "Assigned persona 'high_utilization' to user_001 (confidence: 0.92)"),
        (base_time + timedelta(minutes=9), "INFO", "src.personas.persona_classifier:assign_persona:156", "Assigned persona 'subscription_heavy' to user_012 (confidence: 0.88)"),
        (base_time + timedelta(minutes=9), "INFO", "src.personas.persona_classifier:assign_persona:156", "Assigned persona 'fraud_risk' to user_001 (confidence: 0.95)"),
        (base_time + timedelta(minutes=9), "WARNING", "src.personas.persona_classifier:assign_persona:142", "⚠️ Insufficient data for user_015, assigned 'insufficient_data' persona"),
        
        # Recommendation generation
        (base_time + timedelta(minutes=10), "INFO", "src.recommend.recommendation_engine:generate_recommendations:234", "Generated 5 recommendations for user_001 (persona: fraud_risk)"),
        (base_time + timedelta(minutes=10), "INFO", "src.recommend.recommendation_engine:generate_recommendations:234", "Generated 4 recommendations for user_002 (persona: high_utilization)"),
        (base_time + timedelta(minutes=11), "WARNING", "src.guardrails.guardrails:check_consent:45", "⚠️ Recommendation blocked for user_009: consent_status=False"),
        
        # API requests
        (base_time + timedelta(minutes=15), "INFO", "src.api.routes:get_user_profile:78", "GET /profile/user_001?window=180d - 200 OK (45ms)"),
        (base_time + timedelta(minutes=16), "INFO", "src.api.routes:get_recommendations:112", "GET /recommendations/user_001?max_recommendations=5 - 200 OK (123ms)"),
        (base_time + timedelta(minutes=17), "INFO", "src.api.routes:approve_recommendation:145", "POST /recommendations/rec_abc123/approve - 200 OK (12ms)"),
        (base_time + timedelta(minutes=18), "WARNING", "src.api.routes:get_user_profile:78", "GET /profile/user_999?window=180d - 404 Not Found (8ms)"),
        
        # Database operations
        (base_time + timedelta(minutes=20), "INFO", "src.db.connection:database_transaction:219", "Database operation completed: operation=save_signals, duration_ms=45.2, record_count=1"),
        (base_time + timedelta(minutes=21), "WARNING", "src.db.connection:database_transaction:64", "Database locked, retrying in 0.1s (attempt 1)"),
        (base_time + timedelta(minutes=22), "INFO", "src.db.connection:run_demographic_migration:105", "Applied migration: ALTER TABLE users ADD COLUMN age INTEGER"),
        
        # Performance metrics
        (base_time + timedelta(minutes=25), "INFO", "src.evaluation.metrics:calculate_performance_metrics:189", "Performance metrics calculated: p95_compute_time=234ms, error_rate=2.1%"),
        (base_time + timedelta(minutes=26), "WARNING", "src.evaluation.metrics:calculate_performance_metrics:228", "Slow database operation detected: operation=calculate_fairness_metrics, duration_ms=1245"),
        
        # Data quality issues
        (base_time + timedelta(minutes=30), "WARNING", "src.features.savings:compute_savings_signals:98", "⚠️ Missing account data for user_020, skipping savings computation"),
        (base_time + timedelta(minutes=31), "ERROR", "scripts.compute_signals:compute_user_signals:67", "❌ Error computing signals for user_025: KeyError('monthly_income')"),
        
        # Fairness metrics
        (base_time + timedelta(minutes=35), "INFO", "src.evaluation.metrics:calculate_fairness_metrics:689", "Fairness metrics calculated: 8 demographic groups, parity_cv=7.2%, status=good"),
        (base_time + timedelta(minutes=36), "WARNING", "src.evaluation.metrics:calculate_fairness_metrics:682", "⚠️ Disparity detected: group=25-34_M_Black, rate=45.2%, difference=12.8%"),
        
        # User activity
        (base_time + timedelta(minutes=40), "INFO", "src.ui.components.user_view:mark_recommendation_viewed:89", "User user_001 viewed recommendation rec_abc123"),
        (base_time + timedelta(minutes=41), "INFO", "src.api.routes:mark_viewed:178", "POST /recommendations/rec_abc123/view - 200 OK (5ms)"),
        
        # System health
        (base_time + timedelta(minutes=45), "INFO", "src.ui.streamlit_app:get_system_health:167", "System health check: 30 users, 100.0% signal coverage, avg_quality=0.89"),
        (base_time + timedelta(minutes=50), "WARNING", "src.ui.streamlit_app:get_system_health:167", "⚠️ System health degraded: avg_data_quality=0.42 (threshold: 0.70)"),
        
        # Recent activity
        (base_time + timedelta(hours=1, minutes=30), "INFO", "scripts.generate_recommendations:main:67", "Generating recommendations for all users..."),
        (base_time + timedelta(hours=1, minutes=32), "INFO", "scripts.generate_recommendations:main:72", "✅ Generated recommendations for 28 users (2 skipped: no signals)"),
        (base_time + timedelta(hours=1, minutes=35), "INFO", "src.api.routes:get_recommendations:112", "GET /recommendations/user_005?max_recommendations=5 - 200 OK (98ms)"),
        (base_time + timedelta(hours=1, minutes=40), "DEBUG", "src.recommend.recommendation_engine:_score_content:189", "Content 'credit_utilization_guide' scored 0.87 for user_005 (triggers: high_credit_utilization)"),
        (base_time + timedelta(hours=1, minutes=45), "INFO", "src.guardrails.guardrails:check_eligibility:78", "Eligibility check passed for user_005: content=credit_utilization_guide"),
    ]
    
    for log_time, level, location, message in log_events:
        timestamp = log_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"{timestamp} | {level:7} | {location:50} - {message}\n"
        logs.append(log_line)
    
    return logs

def filter_mock_logs(logs: list, log_level: str) -> list:
    """Filter mock logs by level."""
    if log_level == "All":
        return logs
    
    filtered = []
    for line in logs:
        if f" | {log_level}" in line or f"| {log_level} |" in line:
            filtered.append(line)
    
    return filtered

