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

from src.db.connection import database_transaction, get_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from loguru import logger

def get_available_user_ids() -> list:
    """Get list of all available user IDs from database."""
    try:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        with database_transaction(db_path) as conn:
            results = conn.execute("""
                SELECT DISTINCT user_id 
                FROM users 
                ORDER BY user_id
            """).fetchall()
            return [row['user_id'] for row in results]
    except Exception as e:
        logger.error(f"Error getting user IDs: {e}")
        return []

def get_user_personas(user_ids: list) -> Dict[str, str]:
    """Get persona for each user ID."""
    personas = {}
    try:
        from src.features.schema import UserSignals
        from src.personas.persona_classifier import classify_persona
        from src.db.connection import get_user_signals
        
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        
        for user_id in user_ids:
            try:
                signals_dict = get_user_signals(user_id, "180d", db_path)
                if signals_dict:
                    signals = UserSignals(**signals_dict)
                    persona_match = classify_persona(signals)
                    if persona_match:
                        personas[user_id] = persona_match.persona_id
                    else:
                        personas[user_id] = 'insufficient_data'
                else:
                    personas[user_id] = 'insufficient_data'
            except Exception as e:
                logger.warning(f"Error getting persona for {user_id}: {e}")
                personas[user_id] = 'insufficient_data'
    except Exception as e:
        logger.error(f"Error getting user personas: {e}")
    
    return personas

def get_persona_colors() -> Dict[str, str]:
    """Get color mapping for each persona."""
    return {
        'high_utilization': '#dc3545',      # Red
        'variable_income': '#ffc107',       # Yellow/Amber
        'subscription_heavy': '#fd7e14',     # Orange
        'savings_builder': '#28a745',       # Green
        'fee_fighter': '#007bff',            # Blue
        'fraud_risk': '#e83e8c',             # Pink
        'insufficient_data': '#6c757d'       # Gray
    }

def get_persona_names() -> Dict[str, str]:
    """Get display names for each persona."""
    return {
        'high_utilization': 'High Utilization',
        'variable_income': 'Variable Income',
        'subscription_heavy': 'Subscription Heavy',
        'savings_builder': 'Savings Builder',
        'fee_fighter': 'Fee Fighter',
        'fraud_risk': 'Fraud Risk',
        'insufficient_data': 'Insufficient Data'
    }

def render_user_view():
    """Render user-facing view of recommendations."""
    # Operator call-out: This is a mock of the end-user experience
    st.info("👁️ **Operator View**: This page shows a mock of the end-user web application experience. Use this to preview how personalized recommendations appear to users.")
    
    st.title("💰 My Financial Insights")
    
    # Get available user IDs
    available_user_ids = get_available_user_ids()
    
    # Get personas for all users
    user_personas = get_user_personas(available_user_ids) if available_user_ids else {}
    persona_colors = get_persona_colors()
    persona_names = get_persona_names()
    
    # Use session state to persist user_id
    if 'user_id_to_view' not in st.session_state:
        st.session_state.user_id_to_view = ""
    
    # Check if user is loaded
    user_loaded = bool(st.session_state.get('user_id_to_view'))
    
    if user_loaded:
        # Show back button and current user info
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Back to User List", use_container_width=True):
                st.session_state.user_id_to_view = ""
                st.rerun()
        with col2:
            st.markdown(f"**Viewing:** `{st.session_state.user_id_to_view}`")
        with col3:
            if st.button("🔄 Change User", use_container_width=True):
                st.session_state.user_id_to_view = ""
                st.rerun()
        st.markdown("---")
    else:
        # Show user selection interface
        st.markdown("---")
        
        # User ID input with Enter key support using form
        with st.form("user_id_form", clear_on_submit=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                user_id_input = st.text_input(
                    "Enter Your User ID",
                    value="",
                    placeholder="e.g., user_001",
                    help="Enter your user ID and press Enter or click Load"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
                submitted = st.form_submit_button("🔍 Load My Profile", type="primary")
            
            # Handle form submission (Enter key or button click)
            if submitted and user_id_input:
                st.session_state.user_id_to_view = user_id_input
                st.rerun()
        
        # Show user IDs below form
        if available_user_ids:
            st.markdown("---")
            st.markdown("### 📋 Available Test User IDs")
            
            # Persona legend
            st.markdown("**Persona Colors:**")
            legend_cols = st.columns(7)
            for idx, (persona_id, color) in enumerate(persona_colors.items()):
                with legend_cols[idx % 7]:
                    persona_name = persona_names.get(persona_id, persona_id)
                    legend_html = f"<div style='text-align: center; margin-bottom: 0.5rem;'><div style='width: 30px; height: 30px; background-color: {color}; border: 2px solid {color}; border-radius: 4px; margin: 0 auto 0.25rem;'></div><span style='font-size: 0.75rem; display: block;'>{persona_name}</span></div>"
                    st.markdown(legend_html, unsafe_allow_html=True)
            
            st.markdown("**Click a user ID below to quickly load their profile:**")
            # Display in columns for better layout
            # Define color indicators once
            color_indicators = {
                'high_utilization': '🔴',
                'variable_income': '🟡',
                'subscription_heavy': '🟠',
                'savings_builder': '🟢',
                'fee_fighter': '🔵',
                'fraud_risk': '🟣',
                'insufficient_data': '⚪'
            }
            
            num_cols = min(5, len(available_user_ids))
            cols = st.columns(num_cols)
            for idx, uid in enumerate(available_user_ids):  # Show all users
                persona_id = user_personas.get(uid, 'insufficient_data')
                color = persona_colors.get(persona_id, '#6c757d')
                
                with cols[idx % num_cols]:
                    # Create button with colored border indicator
                    indicator = color_indicators.get(persona_id, '⚪')
                    button_label = f"{indicator} {uid}"
                    button_html = f"<style>button[kind=\"secondary\"][data-testid=\"baseButton-secondary\"][id*=\"main_user_btn_{uid}\"] {{ border: 3px solid {color} !important; border-radius: 0.5rem !important; }}</style>"
                    st.markdown(button_html, unsafe_allow_html=True)
                    
                    if st.button(button_label, key=f"main_user_btn_{uid}", use_container_width=True):
                        st.session_state.user_id_to_view = uid
                        st.rerun()
            st.markdown("---")
        
        st.info("👆 Enter your user ID above, or click one of the user IDs below to see personalized financial insights")
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
            
            # Display consent management
            render_consent_section(user_id)
            
            # Display persona
            render_persona_section(profile)
            
            # Display recommendations
            render_recommendations_section(user_id, profile)
            
    except Exception as e:
        logger.error(f"Error loading user profile: {e}")
        st.error(f"❌ Error loading profile: {str(e)}")
        st.info("💡 Make sure the database is initialized and contains user data")

def get_user_consent_status(user_id: str) -> Optional[bool]:
    """Get user's consent status from database."""
    try:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        with database_transaction(db_path) as conn:
            result = conn.execute("""
                SELECT consent_status FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            if result:
                return bool(result['consent_status'])
            return None
    except Exception as e:
        logger.error(f"Error getting consent status: {e}")
        return None

def toggle_user_consent(user_id: str) -> bool:
    """Toggle user's consent status."""
    try:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        with database_transaction(db_path) as conn:
            # Get current status
            result = conn.execute("""
                SELECT consent_status FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            if not result:
                logger.error(f"User {user_id} not found")
                return False
            
            # Toggle consent
            new_status = not bool(result['consent_status'])
            conn.execute("""
                UPDATE users 
                SET consent_status = ?
                WHERE user_id = ?
            """, (new_status, user_id))
            
            logger.info(f"Toggled consent for {user_id}: {new_status}")
            return True
    except Exception as e:
        logger.error(f"Error toggling consent: {e}")
        return False

def render_consent_section(user_id: str):
    """Render consent management section."""
    # Handle consent toggle
    if st.session_state.get(f'toggle_consent_{user_id}', False):
        st.session_state[f'toggle_consent_{user_id}'] = False  # Reset flag
        
        with st.spinner("Updating consent status..."):
            success = toggle_user_consent(user_id)
        
        if success:
            st.success("✅ Consent status updated!")
            import time
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Failed to update consent status.")
    
    # Get current consent status
    consent_status = get_user_consent_status(user_id)
    
    if consent_status is None:
        st.warning("⚠️ Could not retrieve consent status")
        return
    
    # Display consent status and button
    col1, col2 = st.columns([2, 1])
    with col1:
        if consent_status:
            st.info("✅ **Data Sharing Consent**: You have consented to data sharing. Recommendations are enabled.")
        else:
            st.warning("⚠️ **Data Sharing Consent**: You have not consented to data sharing. Recommendations are disabled.")
    
    with col2:
        button_label = "🚫 Revoke Consent" if consent_status else "✅ Grant Consent"
        button_type = "secondary" if consent_status else "primary"
        
        if st.button(button_label, type=button_type, use_container_width=True,
                     help="Toggle your data sharing consent status"):
            st.session_state[f'toggle_consent_{user_id}'] = True
            st.rerun()
    
    st.markdown("---")

def get_user_profile_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile directly from database."""
    try:
        from src.features.schema import UserSignals
        from src.personas.persona_classifier import classify_persona
        from src.recommend.signal_mapper import map_signals_to_triggers
        from src.db.connection import get_user_signals
        
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        
        # Get signals
        signals_dict = get_user_signals(user_id, "180d", db_path)
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
        'fraud_risk': '🚨',
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
    # Check consent status first - block recommendations if no consent
    consent_status = get_user_consent_status(user_id)
    
    if consent_status is False:
        st.header("💡 Recommendations for You")
        st.warning("""
        ⚠️ **Recommendations are disabled**
        
        You have not consented to data sharing. To receive personalized financial recommendations, 
        please grant consent using the button above.
        """)
        return
    
    # Handle fresh recommendation generation
    if st.session_state.get(f'generate_fresh_recs_{user_id}', False):
        st.session_state[f'generate_fresh_recs_{user_id}'] = False  # Reset flag
        
        st.info("🔄 Generating fresh recommendations... This may take a few seconds.")
        with st.spinner("⏳ Processing..."):
            success = generate_fresh_recommendations(user_id)
        
        if success:
            st.success("✅ New recommendations generated! Refreshing...")
            import time
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed to generate recommendations. Please try again.")
    
    st.header("💡 Recommendations for You")
    
    # Get New Recommendations button - more prominent
    if st.button("🔄 Get New Recommendations", type="primary", use_container_width=True, 
                 help="Generate fresh recommendations based on your latest financial data"):
        st.session_state[f'generate_fresh_recs_{user_id}'] = True
        st.rerun()
    
    try:
        # Get recommendations from database
        recommendations = get_recommendations_from_db(user_id)
        
        if not recommendations:
            st.info("📝 No recommendations available yet. Click 'Get New Recommendations' above to generate personalized recommendations!")
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
    """Get recommendations directly from database.
    
    Returns empty list if user has not consented to data sharing.
    """
    try:
        from src.db.connection import database_transaction
        
        # Check consent first - don't return recommendations if no consent
        consent_status = get_user_consent_status(user_id)
        if consent_status is False:
            logger.info(f"Blocking recommendations for {user_id}: No consent")
            return []
        
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        with database_transaction(db_path) as conn:
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

def _extract_disclaimer(rationale: str, content_type: str) -> str:
    """Extract disclaimer from rationale or provide default."""
    # Disclaimers are appended to rationale, try to extract
    disclaimer_keywords = [
        "This is a partner offer",
        "Results are estimates only",
        "This content is for educational purposes",
        "This checklist is a general guide"
    ]
    
    for keyword in disclaimer_keywords:
        if keyword.lower() in rationale.lower():
            # Find the disclaimer part (usually after the main rationale)
            parts = rationale.split(keyword)
            if len(parts) > 1:
                return keyword + parts[1].rstrip('.')
    
    # Fallback to default based on type
    defaults = {
        'partner_offer': 'This is a partner offer. We may receive compensation if you apply.',
        'calculator': 'Results are estimates only. Consult a financial advisor for personalized advice.',
        'article': 'This content is for educational purposes only and does not constitute financial advice.',
        'checklist': 'This checklist is a general guide. Your situation may vary.'
    }
    return defaults.get(content_type, 'This content is for educational purposes only.')

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
    
    # Extract main rationale (before disclaimer) and disclaimer separately
    rationale = rec['rationale']
    disclaimer = _extract_disclaimer(rationale, rec['type'])
    
    # Remove disclaimer from main rationale for cleaner display
    for keyword in ["This is a partner offer", "Results are estimates only", 
                    "This content is for educational purposes", "This checklist is a general guide"]:
        if keyword.lower() in rationale.lower():
            rationale = rationale.split(keyword)[0].strip().rstrip('.')
            break
    
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
                <p style="margin: 0.5rem 0 0 0;">{rationale}</p>
            </div>
            <div style="background-color: #fff3cd; padding: 0.75rem; border-radius: 0.25rem; margin: 0.75rem 0; border-left: 3px solid #ffc107;">
                <p style="margin: 0; font-size: 0.85rem; color: #856404;">
                    <strong>⚠️ Disclaimer:</strong> {disclaimer}
                </p>
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

def generate_fresh_recommendations(user_id: str) -> bool:
    """Generate fresh recommendations for a user on-demand."""
    try:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        
        # Check consent status first
        consent_status = get_user_consent_status(user_id)
        if consent_status is False:
            logger.warning(f"Cannot generate recommendations for {user_id}: No consent")
            return False
        
        # Get user signals
        signals_dict = get_user_signals(user_id, '180d', db_path)
        if not signals_dict:
            logger.warning(f"No signals found for {user_id}")
            return False
        
        signals = UserSignals(**signals_dict)
        
        # Generate recommendations
        engine = RecommendationEngine()
        recommendations = engine.generate_recommendations(
            user_id=user_id,
            signals=signals,
            max_recommendations=5
        )
        
        if not recommendations:
            logger.warning(f"No recommendations generated for {user_id}")
            return False
        
        # Save to database (this will create new recommendations)
        if save_recommendations(user_id, recommendations, db_path):
            logger.info(f"Generated {len(recommendations)} fresh recommendations for {user_id}")
            return True
        else:
            logger.error(f"Failed to save recommendations for {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error generating fresh recommendations for {user_id}: {e}")
        return False

def mark_recommendation_viewed(rec_id: str):
    """Mark recommendation as viewed."""
    try:
        from src.db.connection import database_transaction
        from datetime import datetime
        
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        with database_transaction(db_path) as conn:
            conn.execute("""
                UPDATE recommendations
                SET viewed_at = ?
                WHERE rec_id = ?
            """, (datetime.now().isoformat(), rec_id))
    except Exception as e:
        logger.warning(f"Could not mark recommendation as viewed: {e}")

