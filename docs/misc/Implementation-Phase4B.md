# SpendSense Implementation Checklist - Phase 4 Subphase B

## 🎯 Purpose
This document implements **Phase 4 Subphase B: Complete Original Spec** - completing all remaining features from the original PRD. Each task is actionable and can be completed in 15-60 minutes with clear validation steps.

**Prerequisites**: Phase 1, 2, 3, and 4A must be complete.

## 📋 How to Use This Checklist
1. ✅ Complete tasks in the **exact order specified**
2. 🚫 **Never skip dependency validation** - if a task's dependencies aren't met, stop and fix them first
3. ⏱️ **Time estimates are conservative** - experienced developers may be faster
4. 🧪 **Run validation after each task** - catch issues early
5. 🔄 **If validation fails**, fix the issue before proceeding

---

## 🚀 PHASE 4B: Complete Original Spec

**Phase Goal**: Complete all remaining features from original PRD  
**Estimated Total Time**: 11-17 hours  
**Success Criteria**: 
- All 7 API endpoints implemented
- All 6 operator dashboard pages functional
- Relevance metrics calculated and displayed

---

### 🔌 **Phase 4B.1: Missing API Endpoints** (2-3 hours)

#### ✅ Task 4B.1.1: Add POST /users Endpoint (30 min)
**Dependencies**: Phase 2 complete (database schema exists)  
**Deliverable**: Updated `src/api/routes.py` with user creation endpoint

**Update `src/api/routes.py`**:

Add request model:
```python
class UserCreateRequest(BaseModel):
    """Request to create a new user."""
    user_id: Optional[str] = None  # Auto-generate if not provided
    consent_status: bool = False  # Default to no consent
```

Add endpoint after `/health`:
```python
@app.post("/users")
async def create_user(request: UserCreateRequest):
    """Create a new user.
    
    Args:
        request: User creation request with optional user_id
    
    Returns:
        Created user information
    """
    try:
        import uuid
        from datetime import datetime
        
        # Generate user_id if not provided
        user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
        
        # Check if user already exists
        with database_transaction() as conn:
            existing = conn.execute("""
                SELECT user_id FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            if existing:
                raise HTTPException(
                    status_code=409, 
                    detail=f"User {user_id} already exists"
                )
            
            # Create user
            conn.execute("""
                INSERT INTO users (user_id, created_at, consent_status, consent_date)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                datetime.now().isoformat(),
                request.consent_status,
                datetime.now().isoformat() if request.consent_status else None
            ))
        
        logger.info(f"Created user: {user_id}")
        
        return {
            "user_id": user_id,
            "consent_status": request.consent_status,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Validation**:
```bash
# Test user creation
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"consent_status": true}'

# Should return: {"user_id": "user_...", "consent_status": true, ...}

# Test duplicate user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "consent_status": false}'

# Should return 409 if user_001 exists
```

**Blockers for**: Consent endpoint

---

#### ✅ Task 4B.1.2: Add POST /consent Endpoint (30 min)
**Dependencies**: Task 4B.1.1  
**Deliverable**: Updated `src/api/routes.py` with consent management endpoint

**Update `src/api/routes.py`**:

Add request model:
```python
class ConsentRequest(BaseModel):
    """Request to update user consent."""
    user_id: str
    consented: bool
    reason: Optional[str] = None  # Optional reason for consent change
```

Add endpoint after `/users`:
```python
@app.post("/consent")
async def update_consent(request: ConsentRequest):
    """Grant or revoke user consent.
    
    Args:
        request: Consent update request
    
    Returns:
        Updated consent status
    """
    try:
        from datetime import datetime
        
        # Check if user exists
        with database_transaction() as conn:
            user = conn.execute("""
                SELECT user_id, consent_status FROM users WHERE user_id = ?
            """, (request.user_id,)).fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User {request.user_id} not found"
                )
            
            # Update consent
            conn.execute("""
                UPDATE users
                SET consent_status = ?,
                    consent_date = ?
                WHERE user_id = ?
            """, (
                request.consented,
                datetime.now().isoformat() if request.consented else None,
                request.user_id
            ))
        
        action = "granted" if request.consented else "revoked"
        logger.info(f"Consent {action} for user {request.user_id}")
        
        return {
            "user_id": request.user_id,
            "consent_status": request.consented,
            "updated_at": datetime.now().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Validation**:
```bash
# Test consent update
curl -X POST http://localhost:8000/consent \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "consented": true}'

# Should return: {"user_id": "user_001", "consent_status": true, ...}

# Verify consent is checked in recommendations
curl http://localhost:8000/recommendations/user_001
# Should work if consented, 403 if not consented
```

**Blockers for**: Feedback endpoint

---

#### ✅ Task 4B.1.3: Add POST /feedback Endpoint (45 min)
**Dependencies**: Task 4B.1.2  
**Deliverable**: Updated `src/api/routes.py` with feedback endpoint and feedback table

**First, update database schema** (`db/schema.sql`):

Add feedback table:
```sql
-- User feedback on recommendations
CREATE TABLE feedback (
    feedback_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    rec_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    helpful BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (rec_id) REFERENCES recommendations(rec_id)
);

CREATE INDEX idx_feedback_user ON feedback(user_id);
CREATE INDEX idx_feedback_rec ON feedback(rec_id);
```

**Run migration**:
```bash
# In container shell
sqlite3 db/spend_sense.db < db/schema.sql
# Or add migration script
```

**Update `src/api/routes.py`**:

Add request model:
```python
class FeedbackRequest(BaseModel):
    """Request to record user feedback."""
    user_id: str
    rec_id: str
    helpful: bool
    comment: Optional[str] = None
```

Add endpoint after `/consent`:
```python
@app.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    """Record user feedback on recommendations.
    
    Args:
        request: Feedback request with user_id, rec_id, helpful flag
    
    Returns:
        Confirmation of feedback recorded
    """
    try:
        import uuid
        from datetime import datetime
        
        # Verify recommendation exists
        with database_transaction() as conn:
            rec = conn.execute("""
                SELECT rec_id, content_id, user_id FROM recommendations WHERE rec_id = ?
            """, (request.rec_id,)).fetchone()
            
            if not rec:
                raise HTTPException(
                    status_code=404,
                    detail=f"Recommendation {request.rec_id} not found"
                )
            
            # Verify user_id matches
            if rec['user_id'] != request.user_id:
                raise HTTPException(
                    status_code=403,
                    detail="User ID does not match recommendation"
                )
            
            # Record feedback
            feedback_id = f"feedback_{uuid.uuid4().hex[:12]}"
            conn.execute("""
                INSERT INTO feedback 
                (feedback_id, user_id, rec_id, content_id, helpful, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id,
                request.user_id,
                request.rec_id,
                rec['content_id'],
                request.helpful,
                request.comment,
                datetime.now().isoformat()
            ))
        
        logger.info(f"Feedback recorded: {feedback_id} (helpful={request.helpful})")
        
        return {
            "feedback_id": feedback_id,
            "rec_id": request.rec_id,
            "helpful": request.helpful,
            "status": "recorded",
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Validation**:
```bash
# Test feedback recording
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "rec_id": "some_rec_id",
    "helpful": true,
    "comment": "Very helpful!"
  }'

# Should return: {"feedback_id": "feedback_...", "status": "recorded", ...}

# Verify feedback stored in database
sqlite3 db/spend_sense.db "SELECT * FROM feedback LIMIT 5;"
```

**Blockers for**: Operator review endpoint

---

#### ✅ Task 4B.1.4: Add GET /operator/review Endpoint (30 min)
**Dependencies**: Task 4B.1.3  
**Deliverable**: Updated `src/api/routes.py` with operator approval queue endpoint

**Update `src/api/routes.py`**:

Add endpoint after `/feedback`:
```python
@app.get("/operator/review")
async def get_approval_queue(
    limit: int = 50,
    status: Optional[str] = None  # "pending", "approved", "rejected", None=all
):
    """Get recommendations awaiting operator approval.
    
    Args:
        limit: Maximum number of recommendations to return
        status: Filter by approval status ("pending", "approved", "rejected")
    
    Returns:
        List of recommendations with approval status
    """
    try:
        from src.recommend.content_schema import load_content_catalog
        
        # Build query based on status
        if status == "pending":
            where_clause = "WHERE approved IS NULL"
        elif status == "approved":
            where_clause = "WHERE approved = 1"
        elif status == "rejected":
            where_clause = "WHERE approved = 0"
        else:
            where_clause = ""
        
        with database_transaction() as conn:
            results = conn.execute(f"""
                SELECT 
                    rec_id,
                    user_id,
                    content_id,
                    rationale,
                    created_at,
                    approved,
                    delivered,
                    viewed_at
                FROM recommendations
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            if not results:
                return {
                    "recommendations": [],
                    "count": 0,
                    "status": status or "all"
                }
            
            # Load content catalog for titles
            catalog = load_content_catalog("data/content/catalog.json")
            
            recommendations = []
            for row in results:
                content_id = row['content_id']
                content_item = next(
                    (item for item in catalog.items if item.content_id == content_id),
                    None
                )
                
                recommendations.append({
                    "rec_id": row['rec_id'],
                    "user_id": row['user_id'],
                    "content_id": content_id,
                    "title": content_item.title if content_item else "Unknown Content",
                    "type": content_item.type if content_item else "unknown",
                    "rationale": row['rationale'],
                    "created_at": row['created_at'],
                    "approved": bool(row['approved']) if row['approved'] is not None else None,
                    "delivered": bool(row['delivered']),
                    "viewed_at": row['viewed_at']
                })
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "status": status or "all"
        }
        
    except Exception as e:
        logger.error(f"Error getting approval queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Validation**:
```bash
# Test approval queue
curl http://localhost:8000/operator/review?status=pending

# Should return: {"recommendations": [...], "count": N, "status": "pending"}

# Test with different statuses
curl http://localhost:8000/operator/review?status=approved&limit=10
```

**Blockers for**: Phase 4B.1 complete

---

### 📊 **Phase 4B.2: Operator Dashboard Pages** (7-11 hours)

#### ✅ Task 4B.2.1: Implement Recommendation Engine Page (2-3 hours)
**Dependencies**: Phase 4B.1.4 (operator review endpoint)  
**Deliverable**: Updated `src/ui/streamlit_app.py` with Recommendation Engine page

**Create `src/ui/pages/recommendation_engine.py`**:
```python
"""
Recommendation Engine page - Review and approve recommendations
"""
import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Any
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from loguru import logger

def render_recommendation_engine():
    """Render recommendation review and approval workflow."""
    st.title("🎯 Recommendation Engine")
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
        if st.button("🔄 Refresh"):
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
        recommendations = get_approval_queue(limit=limit, status=api_status)
        
        if not recommendations:
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

def get_approval_queue(limit: int = 50, status: str = None) -> List[Dict[str, Any]]:
    """Get approval queue from database."""
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
        
        with database_transaction() as conn:
            results = conn.execute(f"""
                SELECT 
                    rec_id,
                    user_id,
                    content_id,
                    rationale,
                    created_at,
                    approved,
                    delivered
                FROM recommendations
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            if not results:
                return []
            
            # Load content catalog
            catalog = load_content_catalog("data/content/catalog.json")
            
            recommendations = []
            for row in results:
                content_id = row['content_id']
                content_item = next(
                    (item for item in catalog.items if item.content_id == content_id),
                    None
                )
                
                recommendations.append({
                    "rec_id": row['rec_id'],
                    "user_id": row['user_id'],
                    "content_id": content_id,
                    "title": content_item.title if content_item else "Unknown",
                    "type": content_item.type if content_item else "unknown",
                    "rationale": row['rationale'],
                    "created_at": row['created_at'],
                    "approved": row['approved'],
                    "delivered": row['delivered']
                })
            
            return recommendations
            
    except Exception as e:
        logger.error(f"Error getting approval queue: {e}")
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
        
        # Approve/Reject buttons (only show if pending)
        if rec['approved'] is None:
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("✅ Approve", key=f"approve_{rec['rec_id']}"):
                    approve_recommendation(rec['rec_id'], approved=True)
                    st.success("Approved!")
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_{rec['rec_id']}"):
                    approve_recommendation(rec['rec_id'], approved=False)
                    st.warning("Rejected!")
                    st.rerun()
        
        st.markdown("---")

def approve_recommendation(rec_id: str, approved: bool):
    """Approve or reject a recommendation."""
    try:
        from src.api.routes import ApprovalRequest
        import requests
        
        # Call API endpoint
        response = requests.post(
            f"http://localhost:8000/recommendations/{rec_id}/approve",
            json={"approved": approved, "reason": "Operator review"}
        )
        response.raise_for_status()
        
        logger.info(f"Recommendation {rec_id} {'approved' if approved else 'rejected'}")
        
    except Exception as e:
        logger.error(f"Error approving recommendation: {e}")
        st.error(f"Error: {str(e)}")
```

**Update `src/ui/streamlit_app.py`**:

Add import:
```python
from src.ui.pages.recommendation_engine import render_recommendation_engine
```

Update routing:
```python
elif selected_page == "Recommendation Engine":
    render_recommendation_engine()
```

**Validation**:
```bash
# Start Streamlit
streamlit run src/ui/streamlit_app.py

# Navigate to "Recommendation Engine" page
# Verify:
# - Pending recommendations display
# - Approve/Reject buttons work
# - Status filters work
```

**Blockers for**: Data Quality page

---

#### ✅ Task 4B.2.2: Implement Data Quality Page (2-3 hours)
**Dependencies**: Phase 3 complete (signal computation working)  
**Deliverable**: `src/ui/pages/data_quality.py` with data quality analysis

**Create `src/ui/pages/data_quality.py`**:
```python
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
    
    # Get data quality metrics
    try:
        metrics = get_data_quality_metrics()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Data Quality", f"{metrics['avg_quality']:.2f}")
        with col2:
            st.metric("Users with Low Quality", metrics['low_quality_count'])
        with col3:
            st.metric("Users with Errors", metrics['error_count'])
        with col4:
            st.metric("Total Users Analyzed", metrics['total_users'])
        
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

def get_data_quality_metrics() -> dict:
    """Get data quality metrics from database."""
    try:
        with database_transaction() as conn:
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
```

**Update `src/ui/streamlit_app.py`**:

Add import and routing:
```python
from src.ui.pages.data_quality import render_data_quality

# In routing:
elif selected_page == "Data Quality":
    render_data_quality()
```

**Validation**:
```bash
# Start Streamlit and navigate to Data Quality page
# Verify:
# - Metrics display correctly
# - Distribution chart shows
# - Low quality users list displays
```

**Blockers for**: Performance Metrics page

---

#### ✅ Task 4B.2.3: Implement Performance Metrics Page (2-3 hours)
**Dependencies**: Phase 3 complete (evaluation metrics exist)  
**Deliverable**: `src/ui/pages/performance_metrics.py` with performance visualization

**Create `src/ui/pages/performance_metrics.py`**:
```python
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
from src.evaluation.metrics import calculate_performance_metrics
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
        
    except Exception as e:
        logger.error(f"Error loading performance metrics: {e}")
        st.error(f"Error: {str(e)}")
```

**Update `src/ui/streamlit_app.py`**:

Add import and routing:
```python
from src.ui.pages.performance_metrics import render_performance_metrics

# In routing:
elif selected_page == "Performance Metrics":
    render_performance_metrics()
```

**Validation**:
```bash
# Start Streamlit and navigate to Performance Metrics page
# Verify metrics display
```

**Blockers for**: System Logs page

---

#### ✅ Task 4B.2.4: Implement System Logs Page (1-2 hours)
**Dependencies**: Phase 3 complete (logging exists)  
**Deliverable**: `src/ui/pages/system_logs.py` with log viewer

**Create `src/ui/pages/system_logs.py`**:
```python
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
```

**Update `src/ui/streamlit_app.py`**:

Add import and routing:
```python
from src.ui.pages.system_logs import render_system_logs

# In routing:
elif selected_page == "System Logs":
    render_system_logs()
```

**Validation**:
```bash
# Start Streamlit and navigate to System Logs page
# Verify logs display
```

**Blockers for**: Relevance metrics

---

### 📈 **Phase 4B.3: Relevance Metrics** (2-3 hours)

#### ✅ Task 4B.3.1: Add Relevance Scoring Function (1-2 hours)
**Dependencies**: Phase 2 complete (recommendations working)  
**Deliverable**: Updated `src/evaluation/metrics.py` with relevance calculation

**Update `src/evaluation/metrics.py`**:

Add relevance calculation:
```python
def calculate_relevance_score(
    content_item: 'ContentItem',
    persona_id: str,
    signal_triggers: List[str]
) -> float:
    """Calculate relevance score for content-persona-trigger alignment.
    
    Args:
        content_item: Content item being recommended
        persona_id: Assigned persona ID
        signal_triggers: List of signal triggers for user
    
    Returns:
        Relevance score (0.0-1.0)
    """
    score = 0.0
    
    # Persona match (40% weight)
    if persona_id in content_item.personas:
        score += 0.4
    
    # Trigger match (30% weight)
    content_triggers = [t.value for t in content_item.signal_triggers]
    matching_triggers = [t for t in signal_triggers if t in content_triggers]
    if content_triggers:
        trigger_match_ratio = len(matching_triggers) / len(content_triggers)
        score += 0.3 * trigger_match_ratio
    
    # Content priority (20% weight)
    # Higher priority = more relevant
    priority_score = min(content_item.priority_score / 10.0, 1.0)
    score += 0.2 * priority_score
    
    # Content type appropriateness (10% weight)
    # Articles for education, checklists for action, calculators for tools
    type_scores = {
        'article': 1.0,
        'checklist': 0.9,
        'calculator': 0.8,
        'partner_offer': 0.7
    }
    type_score = type_scores.get(content_item.type, 0.5)
    score += 0.1 * type_score
    
    return min(score, 1.0)

def calculate_aggregate_relevance() -> dict:
    """Calculate aggregate relevance metrics across all recommendations.
    
    Returns:
        Dictionary with relevance metrics
    """
    try:
        from src.db.connection import database_transaction
        from src.recommend.content_schema import load_content_catalog
        from src.features.schema import UserSignals
        from src.personas.persona_classifier import classify_persona
        from src.recommend.signal_mapper import map_signals_to_triggers
        import json
        
        catalog = load_content_catalog("data/content/catalog.json")
        
        with database_transaction() as conn:
            # Get all recommendations with user signals
            results = conn.execute("""
                SELECT 
                    r.rec_id,
                    r.user_id,
                    r.content_id,
                    us.signals,
                    pa.persona
                FROM recommendations r
                JOIN user_signals us ON r.user_id = us.user_id AND us.window = '180d'
                LEFT JOIN persona_assignments pa ON r.user_id = pa.user_id AND pa.window = '180d'
            """).fetchall()
            
            if not results:
                return {
                    'avg_relevance': 0.0,
                    'high_relevance_count': 0,
                    'low_relevance_count': 0,
                    'total_recommendations': 0
                }
            
            relevance_scores = []
            high_relevance = 0  # >= 0.7
            low_relevance = 0   # < 0.5
            
            for row in results:
                # Parse signals
                signals_dict = json.loads(row['signals'])
                signals = UserSignals(**signals_dict)
                
                # Get persona
                persona_match = classify_persona(signals)
                persona_id = persona_match.persona_id if persona_match else row['persona']
                
                # Get triggers
                triggers = [t.value for t in map_signals_to_triggers(signals)]
                
                # Get content item
                content_item = next(
                    (item for item in catalog.items if item.content_id == row['content_id']),
                    None
                )
                
                if content_item and persona_id:
                    relevance = calculate_relevance_score(
                        content_item,
                        persona_id,
                        triggers
                    )
                    relevance_scores.append(relevance)
                    
                    if relevance >= 0.7:
                        high_relevance += 1
                    elif relevance < 0.5:
                        low_relevance += 1
            
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            return {
                'avg_relevance': avg_relevance,
                'high_relevance_count': high_relevance,
                'low_relevance_count': low_relevance,
                'total_recommendations': len(results),
                'relevance_distribution': {
                    'high (>=0.7)': high_relevance,
                    'medium (0.5-0.7)': len(relevance_scores) - high_relevance - low_relevance,
                    'low (<0.5)': low_relevance
                }
            }
            
    except Exception as e:
        logger.error(f"Error calculating relevance: {e}")
        return {
            'avg_relevance': 0.0,
            'high_relevance_count': 0,
            'low_relevance_count': 0,
            'total_recommendations': 0
        }
```

**Validation**:
```python
# Test relevance calculation
from src.evaluation.metrics import calculate_relevance_score, calculate_aggregate_relevance
from src.recommend.content_schema import ContentItem, ContentType, SignalTrigger

# Create test content
test_content = ContentItem(
    content_id="test",
    type=ContentType.ARTICLE,
    title="Test",
    description="Test",
    personas=["high_utilization"],
    signal_triggers=[SignalTrigger.HIGH_CREDIT_UTILIZATION],
    url="/test",
    reading_time_minutes=5,
    priority_score=8.0
)

# Test relevance
score = calculate_relevance_score(
    test_content,
    "high_utilization",
    ["high_credit_utilization"]
)
print(f"✅ Relevance score: {score:.2f}")
assert 0.0 <= score <= 1.0

# Test aggregate
aggregate = calculate_aggregate_relevance()
print(f"✅ Avg relevance: {aggregate['avg_relevance']:.2f}")
```

**Blockers for**: Display relevance in dashboard

---

#### ✅ Task 4B.3.2: Display Relevance Metrics in Dashboard (1 hour)
**Dependencies**: Task 4B.3.1  
**Deliverable**: Updated Performance Metrics page with relevance metrics

**Update `src/ui/pages/performance_metrics.py`**:

Add relevance section:
```python
# After performance breakdown, add:

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
        import pandas as pd
        dist_df = pd.DataFrame([
            {'category': k, 'count': v}
            for k, v in relevance_metrics['relevance_distribution'].items()
        ])
        st.bar_chart(dist_df.set_index('category'))
        
except Exception as e:
    st.warning(f"Could not load relevance metrics: {e}")
```

**Validation**:
```bash
# Start Streamlit and navigate to Performance Metrics page
# Verify relevance metrics display
```

**Blockers for**: Phase 4B complete

---

## ✅ Phase 4B Validation & Testing

### End-to-End Validation

**1. Test All API Endpoints**:
```bash
# Create user
curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"consent_status": true}'

# Update consent
curl -X POST http://localhost:8000/consent -H "Content-Type: application/json" -d '{"user_id": "user_001", "consented": true}'

# Record feedback
curl -X POST http://localhost:8000/feedback -H "Content-Type: application/json" -d '{"user_id": "user_001", "rec_id": "some_id", "helpful": true}'

# Get approval queue
curl http://localhost:8000/operator/review?status=pending
```

**2. Test Operator Dashboard Pages**:
```bash
# Start Streamlit
streamlit run src/ui/streamlit_app.py

# Test each page:
# - Recommendation Engine: Approve/reject recommendations
# - Data Quality: View quality metrics
# - Performance Metrics: View performance and relevance
# - System Logs: View recent logs
```

**3. Test Relevance Metrics**:
```python
# Run relevance calculation
from src.evaluation.metrics import calculate_aggregate_relevance
metrics = calculate_aggregate_relevance()
print(f"Avg relevance: {metrics['avg_relevance']:.2f}")
```

### Success Criteria

- [ ] All 7 API endpoints implemented and tested
- [ ] All 6 operator dashboard pages functional
- [ ] Relevance metrics calculated and displayed
- [ ] Approval workflow works end-to-end
- [ ] All validation tests pass

---

## 🎯 Phase 4B Complete

**Time Taken**: 11-17 hours  
**Next Phase**: Phase 4C - Submission Polish (demo video, AI tools doc, fairness metrics)

**Deliverables**:
- ✅ All missing API endpoints
- ✅ Complete operator dashboard
- ✅ Relevance metrics

