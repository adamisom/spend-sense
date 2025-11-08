"""
User-facing view for recommendations
Shows personalized persona and recommendations in user-friendly format
"""
import streamlit as st
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from loguru import logger

def render_user_view():
    """Render user-facing view of recommendations."""
    st.title("💰 My Financial Insights")
    st.markdown("---")
    
    # User ID input
    col1, col2 = st.columns([2, 1])
    with col1:
        user_id = st.text_input(
            "Enter Your User ID",
            value="",
            placeholder="e.g., user_001",
            help="Enter your user ID to see personalized recommendations"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("🔍 Load My Profile", type="primary"):
            st.session_state.user_id_to_view = user_id
    
    # Use session state to persist user_id
    if 'user_id_to_view' not in st.session_state:
        st.session_state.user_id_to_view = ""
    
    if not st.session_state.user_id_to_view:
        st.info("👆 Enter your user ID above to see your personalized financial insights")
        return
    
    user_id = st.session_state.user_id_to_view
    
    # Fetch user profile
    try:
        with st.spinner("Loading your financial profile..."):
            # Get profile via database (not API to avoid circular dependency)
            profile = get_user_profile_from_db(user_id)
            
            if not profile:
                st.error(f"❌ User ID '{user_id}' not found. Please check your user ID and try again.")
                return
            
            # Display persona
            render_persona_section(profile)
            
            # Display recommendations
            render_recommendations_section(user_id, profile)
            
    except Exception as e:
        logger.error(f"Error loading user profile: {e}")
        st.error(f"❌ Error loading profile: {str(e)}")
        st.info("💡 Make sure the database is initialized and contains user data")

def get_user_profile_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile directly from database."""
    try:
        from src.features.schema import UserSignals
        from src.personas.persona_classifier import classify_persona
        from src.recommend.signal_mapper import map_signals_to_triggers
        from src.db.connection import get_user_signals
        
        # Get signals
        signals_dict = get_user_signals(user_id, "180d")
        if not signals_dict:
            return None
        
        signals = UserSignals(**signals_dict)
        
        # Classify persona
        persona_match = classify_persona(signals)
        
        # Map to triggers
        triggers = map_signals_to_triggers(signals)
        
        return {
            'user_id': user_id,
            'persona': persona_match,
            'signals': signals,
            'triggers': triggers
        }
    except Exception as e:
        logger.error(f"Error getting profile from DB: {e}")
        return None

def render_persona_section(profile: Dict[str, Any]):
    """Render persona assignment section."""
    persona = profile.get('persona')
    
    if not persona:
        st.warning("⚠️ No persona assigned yet. We need more data to provide personalized insights.")
        return
    
    st.header("🎯 Your Financial Profile")
    
    # Persona card
    persona_name = persona.persona_name if hasattr(persona, 'persona_name') else persona.get('persona_name', 'Unknown')
    persona_id = persona.persona_id if hasattr(persona, 'persona_id') else persona.get('persona_id', 'unknown')
    
    # Color coding by persona
    persona_colors = {
        'high_utilization': '🔴',
        'variable_income': '🟡',
        'subscription_heavy': '🟠',
        'savings_builder': '🟢',
        'fee_fighter': '🔵',
        'insufficient_data': '⚪'
    }
    
    icon = persona_colors.get(persona_id, '💰')
    
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0;">
        <h2 style="margin: 0; color: #1f77b4;">{icon} {persona_name}</h2>
        <p style="margin-top: 0.5rem; color: #666;">Based on your recent financial activity</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Matched criteria
    matched_criteria = persona.matched_criteria if hasattr(persona, 'matched_criteria') else persona.get('matched_criteria', [])
    if matched_criteria:
        st.subheader("Why this profile?")
        for criterion in matched_criteria:
            st.markdown(f"• {criterion}")

def render_recommendations_section(user_id: str, profile: Dict[str, Any]):
    """Render recommendations section."""
    st.header("💡 Recommendations for You")
    
    try:
        # Get recommendations from database
        recommendations = get_recommendations_from_db(user_id)
        
        if not recommendations:
            st.info("📝 No recommendations available yet. Check back soon!")
            return
        
        st.markdown(f"*We've found {len(recommendations)} personalized recommendations based on your financial profile*")
        st.markdown("---")
        
        # Display each recommendation
        for idx, rec in enumerate(recommendations, 1):
            render_recommendation_card(rec, idx)
            
    except Exception as e:
        logger.error(f"Error loading recommendations: {e}")
        st.error(f"Error loading recommendations: {str(e)}")

def get_recommendations_from_db(user_id: str) -> list:
    """Get recommendations directly from database."""
    try:
        from src.db.connection import database_transaction
        
        with database_transaction() as conn:
            # Get recent recommendations (last 30 days, approved or pending)
            results = conn.execute("""
                SELECT 
                    rec_id,
                    content_id,
                    rationale,
                    created_at,
                    approved,
                    delivered
                FROM recommendations
                WHERE user_id = ?
                  AND created_at >= datetime('now', '-30 days')
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,)).fetchall()
            
            if not results:
                return []
            
            # Get content details from catalog
            from src.recommend.content_schema import load_content_catalog
            catalog = load_content_catalog("data/content/catalog.json")
            
            recommendations = []
            for row in results:
                content_id = row['content_id']
                content_item = next((item for item in catalog.items if item.content_id == content_id), None)
                
                if content_item:
                    recommendations.append({
                        'rec_id': row['rec_id'],
                        'content_id': content_id,
                        'title': content_item.title,
                        'description': content_item.description,
                        'type': content_item.type,
                        'url': content_item.url,
                        'reading_time_minutes': content_item.reading_time_minutes,
                        'rationale': row['rationale'],
                        'created_at': row['created_at'],
                        'approved': row['approved']
                    })
            
            return recommendations
            
    except Exception as e:
        logger.error(f"Error getting recommendations from DB: {e}")
        return []

def render_recommendation_card(rec: Dict[str, Any], idx: int):
    """Render a single recommendation card."""
    # Type icons
    type_icons = {
        'article': '📄',
        'checklist': '✅',
        'calculator': '🧮',
        'partner_offer': '🤝'
    }
    
    icon = type_icons.get(rec['type'], '📋')
    type_label = rec['type'].replace('_', ' ').title()
    
    # Card styling
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0; background-color: #ffffff;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
                <h3 style="margin: 0; color: #1f77b4;">{rec['title']}</h3>
            </div>
            <p style="color: #666; margin: 0.5rem 0;">{rec['description']}</p>
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.25rem; margin: 1rem 0;">
                <strong>💡 Why this matters:</strong>
                <p style="margin: 0.5rem 0 0 0;">{rec['rationale']}</p>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                <span style="color: #888; font-size: 0.9rem;">
                    ⏱️ {rec['reading_time_minutes']} min read • {type_label}
                </span>
                <a href="{rec['url']}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #1f77b4; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer;">
                        Learn More →
                    </button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mark as viewed
        mark_recommendation_viewed(rec['rec_id'])

def mark_recommendation_viewed(rec_id: str):
    """Mark recommendation as viewed."""
    try:
        from src.db.connection import database_transaction
        from datetime import datetime
        
        with database_transaction() as conn:
            conn.execute("""
                UPDATE recommendations
                SET viewed_at = ?
                WHERE rec_id = ?
            """, (datetime.now().isoformat(), rec_id))
    except Exception as e:
        logger.warning(f"Could not mark recommendation as viewed: {e}")

