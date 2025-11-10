"""
Data Quality page - Analyze data quality scores and issues
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from loguru import logger

def render_data_quality():
    """Render data quality analysis page."""
    st.title("📊 Data Quality Analysis")
    st.markdown("Monitor data quality scores and identify users with low-quality data")
    
    # Explanation of data quality calculation
    with st.expander("ℹ️ How Data Quality is Calculated", expanded=False):
        st.markdown("""
        **Data Quality Score (0.0 - 1.0)** measures confidence in user signals based on:
        
        **1. Transaction Volume** (score multiplier)
        - < 10 transactions: Score × 0.3 (70% reduction)
        - 10-19 transactions: Score × 0.5 (50% reduction)
        - 20-49 transactions: Score × 0.7 (30% reduction)
        - 50-99 transactions: Score × 0.85 (15% reduction)
        - 100+ transactions: No reduction
        
        **2. Transaction Density** (transactions per day over 180-day window)
        - < 0.1/day (1 per 10 days): Score × 0.6 (40% reduction)
        - 0.1-0.3/day (1 per 3 days): Score × 0.75 (25% reduction)
        - 0.3-0.5/day (1 per 2 days): Score × 0.85 (15% reduction)
        - 0.5+ transactions/day: No reduction
        
        **3. Data Recency** (days since most recent transaction)
        - > 90 days old: Score × 0.5 (50% reduction)
        - 60-90 days old: Score × 0.7 (30% reduction)
        - 30-60 days old: Score × 0.85 (15% reduction)
        - < 30 days old: No reduction
        
        **4. Signal Completeness** (missing critical signals)
        - Missing 3+ critical signals: Score × 0.6 (40% reduction)
        - Missing 2 critical signals: Score × 0.75 (25% reduction)
        - Missing 1 critical signal: Score × 0.9 (10% reduction)
        - Critical signals: credit utilization, subscription spend, savings inflow, income pay gap, bank fees
        
        **5. Computation Errors**
        - Each error: Score × (1.0 - 0.15 × error_count), minimum 0.3
        
        **6. Account Coverage**
        - Missing both credit cards AND savings accounts: Score × 0.8 (20% reduction)
        
        **Final Score**: Multiplicative penalties applied, then clamped to 0.0-1.0 range.
        """)
    
    # Get data quality metrics
    try:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        metrics = get_data_quality_metrics(db_path)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            quality_value = metrics['avg_quality']
            quality_delta = None
            if quality_value == 0.0 and metrics['total_users'] > 0:
                quality_delta = "⚠️ Signals needed"
            st.metric("Avg Data Quality", f"{quality_value:.2f}", delta=quality_delta)
        with col2:
            st.metric("Users with Low Quality", metrics['low_quality_count'])
        with col3:
            st.metric("Users with Errors", metrics['error_count'])
        with col4:
            st.metric("Total Users Analyzed", metrics['total_users'])
        
        # Show warning if no signals
        if metrics['total_users'] == 0:
            st.warning("⚠️ No user signals found in database")
            st.info("""
            **💡 To compute signals:**
            1. Click "🔧 Compute Signals" in the sidebar, OR
            2. Run: `python scripts/compute_signals.py`
            
            Signals are required for data quality analysis and persona classification.
            """)
        
        st.markdown("---")
        
        # Data quality distribution
        st.subheader("📈 Data Quality Distribution")
        quality_df = pd.DataFrame(metrics['quality_distribution'])
        st.bar_chart(quality_df.set_index('range'))
        
        # Low quality users
        st.subheader("⚠️ Users with Low Data Quality (< 0.5)")
        if metrics['low_quality_users']:
            low_quality_df = pd.DataFrame(metrics['low_quality_users'])
            st.dataframe(low_quality_df, use_container_width=True)
        else:
            st.info("✅ No users with low data quality")
        
        # Users with errors
        st.subheader("❌ Users with Computation Errors")
        if metrics['error_users']:
            error_df = pd.DataFrame(metrics['error_users'])
            st.dataframe(error_df, use_container_width=True)
        else:
            st.info("✅ No computation errors")
        
        # Quality trends (if we have historical data)
        st.subheader("📉 Quality Trends")
        st.info("Historical trends will be available once we collect more data over time")
        
    except Exception as e:
        logger.error(f"Error loading data quality: {e}")
        st.error(f"Error: {str(e)}")

def get_data_quality_metrics(db_path: str = None) -> dict:
    """Get data quality metrics from database."""
    if db_path is None:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
    try:
        with database_transaction(db_path) as conn:
            # Get all signals with quality scores
            results = conn.execute("""
                SELECT 
                    user_id,
                    window,
                    signals,
                    computed_at
                FROM user_signals
                WHERE window = '180d'
            """).fetchall()
            
            if not results:
                return {
                    'avg_quality': 0.0,
                    'low_quality_count': 0,
                    'error_count': 0,
                    'total_users': 0,
                    'quality_distribution': [],
                    'low_quality_users': [],
                    'error_users': []
                }
            
            # Parse signals and extract quality metrics
            quality_scores = []
            low_quality_users = []
            error_users = []
            
            for row in results:
                signals = json.loads(row['signals'])
                quality_score = signals.get('data_quality_score', 0.0)
                quality_scores.append(quality_score)
                
                # Track low quality users
                if quality_score < 0.5:
                    low_quality_users.append({
                        'user_id': row['user_id'],
                        'quality_score': quality_score,
                        'computed_at': row['computed_at']
                    })
                
                # Track users with errors
                errors = signals.get('computation_errors', [])
                if errors:
                    error_users.append({
                        'user_id': row['user_id'],
                        'errors': ', '.join(errors),
                        'quality_score': quality_score
                    })
            
            # Calculate distribution
            distribution = {
                '0.0-0.2': sum(1 for q in quality_scores if 0.0 <= q < 0.2),
                '0.2-0.4': sum(1 for q in quality_scores if 0.2 <= q < 0.4),
                '0.4-0.6': sum(1 for q in quality_scores if 0.4 <= q < 0.6),
                '0.6-0.8': sum(1 for q in quality_scores if 0.6 <= q < 0.8),
                '0.8-1.0': sum(1 for q in quality_scores if 0.8 <= q <= 1.0)
            }
            
            quality_distribution = [
                {'range': k, 'count': v} for k, v in distribution.items()
            ]
            
            return {
                'avg_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
                'low_quality_count': len(low_quality_users),
                'error_count': len(error_users),
                'total_users': len(results),
                'quality_distribution': quality_distribution,
                'low_quality_users': low_quality_users,
                'error_users': error_users
            }
            
    except Exception as e:
        logger.error(f"Error getting data quality metrics: {e}")
        return {
            'avg_quality': 0.0,
            'low_quality_count': 0,
            'error_count': 0,
            'total_users': 0,
            'quality_distribution': [],
            'low_quality_users': [],
            'error_users': []
        }

