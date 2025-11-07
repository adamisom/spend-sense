"""
Performance Metrics page - System performance monitoring
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from loguru import logger

def render_performance_metrics():
    """Render performance metrics page."""
    st.title("⚡ Performance Metrics")
    st.markdown("Monitor system performance and response times")
    
    try:
        # Calculate performance metrics
        metrics = calculate_performance_metrics()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("P95 Compute Time", f"{metrics.get('p95_compute_time_ms', 0):.0f}ms")
        with col2:
            st.metric("Error Rate", f"{metrics.get('error_rate', 0):.1f}%")
        with col3:
            st.metric("Avg Response Time", f"{metrics.get('avg_response_time_ms', 0):.0f}ms")
        with col4:
            st.metric("Total Requests", metrics.get('total_requests', 0))
        
        st.markdown("---")
        
        # Performance breakdown
        st.subheader("📊 Performance Breakdown")
        
        # Compute time distribution
        if 'compute_time_distribution' in metrics:
            compute_df = pd.DataFrame(metrics['compute_time_distribution'])
            st.bar_chart(compute_df.set_index('range'))
        
        # Error rate over time (if we have historical data)
        st.subheader("📉 Error Rate Trends")
        st.info("Historical error trends will be available once we collect more data")
        
        # API endpoint performance
        st.subheader("🔌 API Endpoint Performance")
        if 'endpoint_performance' in metrics:
            endpoint_df = pd.DataFrame(metrics['endpoint_performance'])
            st.dataframe(endpoint_df, use_container_width=True)
        
        # Relevance metrics
        st.subheader("🎯 Recommendation Relevance")
        try:
            from src.evaluation.metrics import calculate_aggregate_relevance
            
            relevance_metrics = calculate_aggregate_relevance()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Relevance", f"{relevance_metrics['avg_relevance']:.2f}")
            with col2:
                st.metric("High Relevance", relevance_metrics['high_relevance_count'])
            with col3:
                st.metric("Low Relevance", relevance_metrics['low_relevance_count'])
            
            # Relevance distribution
            if 'relevance_distribution' in relevance_metrics:
                dist_df = pd.DataFrame([
                    {'category': k, 'count': v}
                    for k, v in relevance_metrics['relevance_distribution'].items()
                ])
                st.bar_chart(dist_df.set_index('category'))
                
        except Exception as e:
            st.warning(f"Could not load relevance metrics: {e}")
        
    except Exception as e:
        logger.error(f"Error loading performance metrics: {e}")
        st.error(f"Error: {str(e)}")

def calculate_performance_metrics() -> dict:
    """Calculate performance metrics from database."""
    try:
        with database_transaction() as conn:
            # Get recommendation generation times (if we track them)
            # For now, return basic metrics
            total_recs = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
            
            return {
                'p95_compute_time_ms': 0,  # Would need timing data
                'error_rate': 0.0,  # Would need error tracking
                'avg_response_time_ms': 0,  # Would need API timing
                'total_requests': total_recs,
                'compute_time_distribution': [],
                'endpoint_performance': []
            }
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        return {
            'p95_compute_time_ms': 0,
            'error_rate': 0.0,
            'avg_response_time_ms': 0,
            'total_requests': 0,
            'compute_time_distribution': [],
            'endpoint_performance': []
        }

