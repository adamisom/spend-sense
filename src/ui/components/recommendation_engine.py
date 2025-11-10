"""
Recommendation Engine page - Review and approve recommendations
"""
import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from loguru import logger

def render_recommendation_engine():
    """Render recommendation review and approval workflow."""
    st.title("🎯 Recommendation Engine")
    
    # Page explanation
    with st.expander("ℹ️ What is this page?", expanded=False):
        st.markdown("""
        **Recommendation Engine** is the operator workflow for reviewing and approving recommendations.
        
        - **Review Queue**: See all generated recommendations with their rationale and match reasons
        - **Approve/Reject**: Manually approve or reject recommendations before they're delivered to users
        - **Status Filtering**: Filter by pending, approved, or rejected status
        - **Quality Control**: Review recommendations to ensure they're appropriate and relevant
        
        **Note**: In the current implementation, recommendations are shown to users regardless of approval status. 
        This page provides oversight and quality control capabilities for operators.
        """)
    
    st.markdown("Review and approve recommendations before delivery")
    
    # Status filter
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Pending", "Approved", "Rejected"],
            help="Filter recommendations by approval status"
        )
    with col2:
        limit = st.number_input("Limit", min_value=10, max_value=200, value=50, step=10)
    with col3:
        if st.button("🔄 Refresh", help="Refresh the recommendation list to see the latest data"):
            st.rerun()
    
    # Map filter to API status
    status_map = {
        "All": None,
        "Pending": "pending",
        "Approved": "approved",
        "Rejected": "rejected"
    }
    api_status = status_map[status_filter]
    
    # Fetch recommendations
    try:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
        recommendations = get_approval_queue(limit=limit, status=api_status, db_path=db_path)
        
        if not recommendations:
            # Show helpful debug info
            import sqlite3
            try:
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    total_count = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
                    pending_count = conn.execute("SELECT COUNT(*) FROM recommendations WHERE approved IS NULL").fetchone()[0]
                    approved_count = conn.execute("SELECT COUNT(*) FROM recommendations WHERE approved = 1").fetchone()[0]
                    rejected_count = conn.execute("SELECT COUNT(*) FROM recommendations WHERE approved = 0").fetchone()[0]
                
                st.info(f"📝 No recommendations found with current filters")
                st.caption(f"**Database stats:** Total: {total_count} | Pending: {pending_count} | Approved: {approved_count} | Rejected: {rejected_count}")
                if status_filter != "All":
                    st.caption(f"💡 Try changing the status filter to 'All' to see all recommendations")
            except Exception as e:
                logger.error(f"Error getting debug stats: {e}")
                st.info("📝 No recommendations found")
            return
        
        st.subheader(f"📋 {len(recommendations)} Recommendations")
        st.markdown("---")
        
        # Display recommendations
        for idx, rec in enumerate(recommendations, 1):
            render_recommendation_review_card(rec, idx)
            
    except Exception as e:
        logger.error(f"Error loading recommendations: {e}")
        st.error(f"Error loading recommendations: {str(e)}")

def get_approval_queue(limit: int = 50, status: str = None, db_path: str = None) -> List[Dict[str, Any]]:
    """Get approval queue from database."""
    if db_path is None:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
    try:
        from src.recommend.content_schema import load_content_catalog
        
        # Build query
        if status == "pending":
            where_clause = "WHERE approved IS NULL"
        elif status == "approved":
            where_clause = "WHERE approved = 1"
        elif status == "rejected":
            where_clause = "WHERE approved = 0"
        else:
            where_clause = ""
        
        logger.info(f"Fetching recommendations: status={status}, limit={limit}, where={where_clause}")
        
        with database_transaction(db_path) as conn:
            # Check if decision_trace column exists
            cursor = conn.execute("PRAGMA table_info(recommendations)")
            columns = [row[1] for row in cursor.fetchall()]
            has_decision_trace = 'decision_trace' in columns
            
            # Build query based on available columns
            if has_decision_trace:
                query = f"""
                    SELECT 
                        rec_id,
                        user_id,
                        content_id,
                        rationale,
                        created_at,
                        approved,
                        delivered,
                        decision_trace
                    FROM recommendations
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ?
                """
            else:
                # Fallback query without decision_trace
                logger.info("decision_trace column not found, using fallback query")
                query = f"""
                    SELECT 
                        rec_id,
                        user_id,
                        content_id,
                        rationale,
                        created_at,
                        approved,
                        delivered,
                        NULL as decision_trace
                    FROM recommendations
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ?
                """
            
            logger.debug(f"Executing query: {query}")
            results = conn.execute(query, (limit,)).fetchall()
            
            logger.info(f"Query returned {len(results)} rows")
            
            if not results:
                logger.warning("No results from database query")
                return []
            
            # Load content catalog
            try:
                catalog = load_content_catalog("data/content/catalog.json")
                logger.info(f"Loaded content catalog with {len(catalog.items)} items")
            except Exception as e:
                logger.error(f"Error loading content catalog: {e}")
                # Continue anyway - we'll use fallback values
                catalog = None
            
            recommendations = []
            missing_content = []
            for row in results:
                content_id = row['content_id']
                
                # Try to find content item in catalog
                content_item = None
                if catalog:
                    content_item = next(
                        (item for item in catalog.items if item.content_id == content_id),
                        None
                    )
                
                # Track missing content items for debugging
                if not content_item:
                    missing_content.append(content_id)
                    logger.warning(f"Content item not found in catalog: {content_id}")
                
                # Parse decision_trace if present
                decision_trace = None
                try:
                    # sqlite3.Row doesn't have .get(), use try/except instead
                    trace_value = row['decision_trace']
                    if trace_value:
                        import json
                        try:
                            decision_trace = json.loads(trace_value)
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Error parsing decision_trace: {e}")
                            decision_trace = None
                except (KeyError, IndexError):
                    # Column doesn't exist or is None
                    decision_trace = None
                
                recommendations.append({
                    "rec_id": row['rec_id'],
                    "user_id": row['user_id'],
                    "content_id": content_id,
                    "title": content_item.title if content_item else f"Unknown ({content_id})",
                    "type": content_item.type.value if content_item and hasattr(content_item.type, 'value') else (content_item.type if content_item else "unknown"),
                    "rationale": row['rationale'],
                    "created_at": row['created_at'],
                    "approved": row['approved'],
                    "delivered": row['delivered'],
                    "decision_trace": decision_trace
                })
            
            # Log if any content items are missing
            if missing_content:
                logger.warning(f"Missing content items in catalog: {missing_content[:5]}")
            
            logger.info(f"Returning {len(recommendations)} recommendations")
            return recommendations
            
    except Exception as e:
        logger.error(f"Error getting approval queue: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return []

def render_recommendation_review_card(rec: Dict[str, Any], idx: int):
    """Render a recommendation review card with approve/reject buttons."""
    # Status badge
    if rec['approved'] is None:
        status_badge = "⏳ Pending"
        status_color = "#ffc107"
    elif rec['approved']:
        status_badge = "✅ Approved"
        status_color = "#28a745"
    else:
        status_badge = "❌ Rejected"
        status_color = "#dc3545"
    
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; color: #1f77b4;">#{idx}: {rec['title']}</h3>
                <span style="background-color: {status_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 0.25rem; font-size: 0.9rem;">
                    {status_badge}
                </span>
            </div>
            <p><strong>User:</strong> {rec['user_id']}</p>
            <p><strong>Type:</strong> {rec['type'].replace('_', ' ').title()}</p>
            <p><strong>Created:</strong> {rec['created_at']}</p>
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.25rem; margin: 1rem 0;">
                <strong>Rationale:</strong>
                <p style="margin: 0.5rem 0 0 0;">{rec['rationale']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Decision Trace (auditability)
        if rec.get('decision_trace'):
            with st.expander("🔍 View Decision Trace (Audit Trail)", expanded=False):
                trace = rec['decision_trace']
                st.markdown("**Full audit trail of how this recommendation was generated:**")
                st.json(trace)
                
                # Show step-by-step summary
                if 'steps' in trace:
                    st.markdown("**Step-by-Step Summary:**")
                    for step in trace['steps']:
                        step_num = step.get('step', '?')
                        action = step.get('action', 'unknown')
                        result = step.get('result', {})
                        
                        st.markdown(f"**Step {step_num}: {action.replace('_', ' ').title()}**")
                        if isinstance(result, dict):
                            # Show key results
                            if 'persona_id' in result:
                                st.caption(f"→ Persona: {result.get('persona_name', result.get('persona_id'))} (confidence: {result.get('confidence', 'N/A')})")
                            if 'triggers' in result:
                                st.caption(f"→ Triggers: {', '.join(result['triggers'])}")
                            if 'candidate_count' in result:
                                st.caption(f"→ Found {result['candidate_count']} candidate items")
                            if 'eligible_count' in result:
                                st.caption(f"→ {result['eligible_count']} items passed eligibility check")
                            if 'final_score' in result:
                                st.caption(f"→ Final score: {result['final_score']}")
                        st.markdown("---")
        
        # Approve/Reject buttons (only show if pending)
        if rec['approved'] is None:
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("✅ Approve", key=f"approve_{rec['rec_id']}"):
                    db_path = st.session_state.get('db_path', 'db/spend_sense.db')
                    approve_recommendation(rec['rec_id'], approved=True, db_path=db_path)
                    st.success("Approved!")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{rec['rec_id']}"):
                    db_path = st.session_state.get('db_path', 'db/spend_sense.db')
                    approve_recommendation(rec['rec_id'], approved=False, db_path=db_path)
                    st.warning("Rejected!")
                    st.rerun()
        
        st.markdown("---")

def approve_recommendation(rec_id: str, approved: bool, db_path: str = None):
    """Approve or reject a recommendation."""
    if db_path is None:
        db_path = st.session_state.get('db_path', 'db/spend_sense.db')
    try:
        from src.db.connection import database_transaction
        
        with database_transaction(db_path) as conn:
            conn.execute("""
                UPDATE recommendations 
                SET approved = ?, delivered = ?
                WHERE rec_id = ?
            """, (approved, approved, rec_id))
        
        logger.info(f"Recommendation {rec_id} {'approved' if approved else 'rejected'}")
        
    except Exception as e:
        logger.error(f"Error approving recommendation: {e}")
        st.error(f"Error: {str(e)}")

