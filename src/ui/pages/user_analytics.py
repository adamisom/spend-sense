"""
User Analytics page for Streamlit dashboard
Provides detailed user insights and persona analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List

from src.db.connection import database_transaction
from src.personas.persona_classifier import classify_persona
from src.features.schema import UserSignals
from loguru import logger

def get_user_data(db_path: str) -> pd.DataFrame:
    """Get comprehensive user data for analytics."""
    try:
        with database_transaction(db_path) as conn:
            # Get users with their latest signals and recommendations
            query = """
            SELECT 
                u.user_id,
                u.consent_status,
                s.window,
                s.signals,
                s.computed_at as signals_computed_at,
                COUNT(DISTINCT r.rec_id) as total_recommendations,
                MAX(r.created_at) as last_recommendation_at
            FROM users u
            LEFT JOIN user_signals s ON u.user_id = s.user_id AND s.window = '180d'
            LEFT JOIN recommendations r ON u.user_id = r.user_id
            GROUP BY u.user_id, u.consent_status, s.window, s.signals, s.computed_at
            ORDER BY u.user_id
            """
            
            df = pd.read_sql_query(query, conn)
            
            # Parse signals JSON
            if not df.empty and 'signals' in df.columns:
                df['parsed_signals'] = df['signals'].apply(
                    lambda x: json.loads(x) if x else {}
                )
                
                # Extract key signal metrics
                df['data_quality_score'] = df['parsed_signals'].apply(
                    lambda x: x.get('data_quality_score', 0.0)
                )
                df['insufficient_data'] = df['parsed_signals'].apply(
                    lambda x: x.get('insufficient_data', True)
                )
                df['subscription_count'] = df['parsed_signals'].apply(
                    lambda x: x.get('subscription_count', 0)
                )
                df['credit_utilization_max'] = df['parsed_signals'].apply(
                    lambda x: x.get('credit_utilization_max')
                )
            else:
                # Add empty columns for consistency
                df['data_quality_score'] = 0.0
                df['insufficient_data'] = True
                df['subscription_count'] = 0
                df['credit_utilization_max'] = None
            
            return df
            
    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        return pd.DataFrame()

def get_persona_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of users across personas."""
    if df.empty:
        return {}
    
    try:
        persona_counts = {}
        
        for _, row in df.iterrows():
            if row.get('parsed_signals'):
                try:
                    # Convert parsed signals back to UserSignals object for classification
                    signals = UserSignals(**row['parsed_signals'])
                    persona_match = classify_persona(signals)
                    if persona_match:
                        persona_id = persona_match.persona_id
                        persona_counts[persona_id] = persona_counts.get(persona_id, 0) + 1
                except Exception as e:
                    logger.warning(f"Error classifying persona for user {row.get('user_id')}: {e}")
                    continue
        
        return persona_counts
        
    except Exception as e:
        logger.error(f"Error getting persona distribution: {e}")
        return {}

def render_user_overview(df: pd.DataFrame):
    """Render user overview section."""
    st.subheader("👥 User Overview")
    
    if df.empty:
        st.warning("No user data available")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(df)
        st.metric("Total Users", f"{total_users:,}")
    
    with col2:
        consented_users = df['consent_status'].sum() if 'consent_status' in df.columns else 0
        consent_rate = (consented_users / total_users * 100) if total_users > 0 else 0
        st.metric("Consent Rate", f"{consent_rate:.1f}%", f"{consented_users}/{total_users}")
    
    with col3:
        users_with_signals = df['insufficient_data'].apply(lambda x: not x).sum()
        signal_rate = (users_with_signals / total_users * 100) if total_users > 0 else 0
        st.metric("Users with Good Signals", f"{signal_rate:.1f}%", f"{users_with_signals}/{total_users}")
    
    with col4:
        users_with_recs = (df['total_recommendations'] > 0).sum()
        rec_rate = (users_with_recs / total_users * 100) if total_users > 0 else 0
        st.metric("Users with Recommendations", f"{rec_rate:.1f}%", f"{users_with_recs}/{total_users}")

def render_persona_analysis(df: pd.DataFrame):
    """Render persona distribution analysis."""
    st.subheader("🎭 Persona Distribution")
    
    persona_dist = get_persona_distribution(df)
    
    if not persona_dist:
        st.warning("No persona data available")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Persona pie chart
        personas = list(persona_dist.keys())
        counts = list(persona_dist.values())
        
        fig = px.pie(
            values=counts, 
            names=personas,
            title="User Distribution by Persona",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Persona table
        st.markdown("**Persona Breakdown:**")
        for persona, count in sorted(persona_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / sum(counts) * 100) if sum(counts) > 0 else 0
            st.markdown(f"- **{persona.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)")

def render_data_quality_analysis(df: pd.DataFrame):
    """Render data quality analysis."""
    st.subheader("📊 Data Quality Analysis")
    
    if df.empty or 'data_quality_score' not in df.columns:
        st.warning("No data quality information available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Data quality distribution
        fig = px.histogram(
            df, 
            x='data_quality_score',
            nbins=20,
            title="Data Quality Score Distribution",
            labels={'data_quality_score': 'Data Quality Score', 'count': 'Number of Users'}
        )
        fig.update_traces(marker_color='lightblue', marker_line_color='darkblue', marker_line_width=1)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Data quality metrics
        avg_quality = df['data_quality_score'].mean()
        median_quality = df['data_quality_score'].median()
        low_quality_users = (df['data_quality_score'] < 0.3).sum()
        high_quality_users = (df['data_quality_score'] >= 0.7).sum()
        
        st.markdown("**Quality Metrics:**")
        st.markdown(f"- **Average Score**: {avg_quality:.3f}")
        st.markdown(f"- **Median Score**: {median_quality:.3f}")
        st.markdown(f"- **Low Quality** (<0.3): {low_quality_users} users")
        st.markdown(f"- **High Quality** (≥0.7): {high_quality_users} users")

def render_signal_insights(df: pd.DataFrame):
    """Render signal-based insights."""
    st.subheader("🔍 Signal Insights")
    
    if df.empty or 'parsed_signals' not in df.columns:
        st.warning("No signal data available")
        return
    
    # Extract signal statistics
    col1, col2 = st.columns(2)
    
    with col1:
        # Credit utilization distribution
        credit_utils = df['credit_utilization_max'].dropna()
        if not credit_utils.empty:
            # Convert Series to DataFrame for px.histogram
            credit_df = pd.DataFrame({'credit_utilization': credit_utils})
            fig = px.histogram(
                credit_df,
                x='credit_utilization',
                nbins=20,
                title="Credit Utilization Distribution",
                labels={'credit_utilization': 'Credit Utilization', 'count': 'Number of Users'}
            )
            fig.add_vline(x=0.3, line_dash="dash", line_color="orange", 
                         annotation_text="30% (Recommended)")
            fig.add_vline(x=0.9, line_dash="dash", line_color="red", 
                         annotation_text="90% (High Risk)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No credit utilization data available")
    
    with col2:
        # Subscription count distribution
        sub_counts = df['subscription_count']
        if not sub_counts.empty:
            # Convert Series to DataFrame for px.histogram
            sub_df = pd.DataFrame({'subscription_count': sub_counts})
            nbins = max(10, int(sub_counts.max()) + 1) if sub_counts.max() > 0 else 10
            fig = px.histogram(
                sub_df,
                x='subscription_count',
                nbins=nbins,
                title="Subscription Count Distribution", 
                labels={'subscription_count': 'Number of Subscriptions', 'count': 'Number of Users'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No subscription data available")

def render_user_list(df: pd.DataFrame):
    """Render detailed user list."""
    st.subheader("📋 User Details")
    
    if df.empty:
        st.warning("No user data available")
        return
    
    # User search/filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("🔍 Search User ID", placeholder="Enter user ID...")
    
    with col2:
        quality_filter = st.selectbox(
            "📊 Data Quality Filter",
            ["All", "High (≥0.7)", "Medium (0.3-0.7)", "Low (<0.3)"]
        )
    
    with col3:
        show_count = st.selectbox("📄 Show", [10, 25, 50, 100], index=1)
    
    # Apply filters
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['user_id'].astype(str).str.contains(search_term, case=False, na=False)]
    
    if quality_filter != "All":
        if quality_filter == "High (≥0.7)":
            filtered_df = filtered_df[filtered_df['data_quality_score'] >= 0.7]
        elif quality_filter == "Medium (0.3-0.7)":
            filtered_df = filtered_df[(filtered_df['data_quality_score'] >= 0.3) & (filtered_df['data_quality_score'] < 0.7)]
        elif quality_filter == "Low (<0.3)":
            filtered_df = filtered_df[filtered_df['data_quality_score'] < 0.3]
    
    # Display results
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} users**")
    
    if not filtered_df.empty:
        # Prepare display DataFrame
        display_df = filtered_df[['user_id', 'consent_status', 'data_quality_score', 
                                 'subscription_count', 'total_recommendations']].head(show_count)
        
        # Format for display
        display_df = display_df.copy()
        display_df['consent_status'] = display_df['consent_status'].apply(lambda x: '✅ Yes' if x else '❌ No')
        display_df['data_quality_score'] = display_df['data_quality_score'].apply(lambda x: f"{x:.3f}")
        
        display_df.columns = ['User ID', 'Consent', 'Data Quality', 'Subscriptions', 'Recommendations']
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No users match the current filters")

def render_user_analytics():
    """Main function to render user analytics page."""
    st.title("👥 User Analytics")
    st.markdown("Comprehensive analysis of user data, personas, and signal quality")
    
    # Load user data
    df = get_user_data(st.session_state.db_path)
    
    if df.empty:
        st.error("No user data found. Please ensure the database is populated and the path is correct.")
        st.info("💡 **Tip**: Use the data generator and signal computation tools to create sample data.")
        return
    
    # Render different sections
    render_user_overview(df)
    st.markdown("---")
    
    render_persona_analysis(df)
    st.markdown("---")
    
    render_data_quality_analysis(df)
    st.markdown("---")
    
    render_signal_insights(df)
    st.markdown("---")
    
    render_user_list(df)

# Streamlit multi-page routing: When accessed via /user_analytics URL,
# Streamlit executes this file directly and runs module-level code.
# Initialize session state and render the page.
if 'db_path' not in st.session_state:
    st.session_state.db_path = "db/spend_sense.db"

# Render the page (executes when file is run as a Streamlit page)
# Note: This also executes on import, but Streamlit's execution model handles this correctly
try:
    render_user_analytics()
except Exception as e:
    st.error(f"Error rendering User Analytics: {e}")
    logger.exception("Error in user_analytics page")

