"""
FastAPI routes for SpendSense
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger
import time

from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona, PersonaMatch
from src.recommend.recommendation_engine import RecommendationEngine, Recommendation
from src.recommend.signal_mapper import map_signals_to_triggers
from src.db.connection import database_transaction, get_user_signals
from src.guardrails.guardrails import guardrails, GuardrailViolation

app = FastAPI(
    title="SpendSense API",
    description="Explainable Financial Education Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

# Request/Response models
class RecommendationResponse(BaseModel):
    """API response for recommendations."""
    user_id: str
    recommendations: List[Dict[str, Any]]
    generated_at: str
    persona: Optional[str] = None

class ProfileResponse(BaseModel):
    """API response for user profile."""
    user_id: str
    persona: Optional[Dict[str, Any]] = None
    signals: Optional[Dict[str, Any]] = None
    triggers: Optional[List[str]] = None

class ApprovalRequest(BaseModel):
    """Request to approve/reject a recommendation."""
    approved: bool
    reason: Optional[str] = None

class UserCreateRequest(BaseModel):
    """Request to create a new user."""
    user_id: Optional[str] = None  # Auto-generate if not provided
    consent_status: bool = False  # Default to no consent

class ConsentRequest(BaseModel):
    """Request to update user consent."""
    user_id: str
    consented: bool
    reason: Optional[str] = None  # Optional reason for consent change

class FeedbackRequest(BaseModel):
    """Request to record user feedback."""
    user_id: str
    rec_id: str
    helpful: bool
    comment: Optional[str] = None

# Helper functions
def check_user_consent(user_id: str) -> bool:
    """Check if user has consented to recommendations."""
    try:
        with database_transaction() as conn:
            result = conn.execute("""
                SELECT consent_status FROM users WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            if result:
                return bool(result['consent_status'])
            return False
    except Exception as e:
        logger.error(f"Error checking consent for {user_id}: {e}")
        return False

def get_user_signals_from_db(user_id: str, window: str = "180d") -> Optional[UserSignals]:
    """Get user signals from database."""
    try:
        signals_dict = get_user_signals(user_id, window)
        if signals_dict:
            return UserSignals(**signals_dict)
        return None
    except Exception as e:
        logger.error(f"Error getting signals for {user_id}: {e}")
        return None

# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SpendSense API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

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

@app.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_user_profile(user_id: str, window: str = "180d"):
    """Get user profile with persona and signals.
    
    Args:
        user_id: User identifier
        window: Time window for signals ("30d" or "180d")
    
    Returns:
        ProfileResponse with persona, signals, and triggers
    """
    try:
        # Get user signals
        signals = get_user_signals_from_db(user_id, window)
        if not signals:
            raise HTTPException(status_code=404, detail=f"No signals found for user {user_id}")
        
        # Classify persona
        persona_match = classify_persona(signals)
        
        # Map signals to triggers
        triggers = map_signals_to_triggers(signals)
        
        return ProfileResponse(
            user_id=user_id,
            persona={
                "persona_id": persona_match.persona_id if persona_match else None,
                "persona_name": persona_match.persona_name if persona_match else None,
                "priority": persona_match.priority if persona_match else None,
                "confidence": persona_match.confidence if persona_match else None,
                "matched_criteria": persona_match.matched_criteria if persona_match else []
            } if persona_match else None,
            signals=signals.model_dump(),
            triggers=[t.value for t in triggers]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: str,
    window: str = "180d",
    max_recommendations: int = 5
):
    """Get personalized recommendations for a user.
    
    Args:
        user_id: User identifier
        window: Time window for signals ("30d" or "180d")
        max_recommendations: Maximum number of recommendations
    
    Returns:
        RecommendationResponse with recommendations and persona
    """
    start_time = time.time()
    
    try:
        # Check consent via guardrails
        try:
            guardrails.check_consent(user_id)
        except GuardrailViolation as e:
            raise HTTPException(status_code=403, detail=e.reason)
        
        # Check rate limit
        try:
            guardrails.check_rate_limit(user_id)
        except GuardrailViolation as e:
            logger.warning(e.reason)
            # Don't block, just log warning
        
        # Get user signals
        signals = get_user_signals_from_db(user_id, window)
        if not signals:
            raise HTTPException(status_code=404, detail=f"No signals found for user {user_id}")
        
        # Classify persona
        persona_match = classify_persona(signals)
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            user_id=user_id,
            signals=signals,
            max_recommendations=max_recommendations
        )
        
        # Apply guardrails filtering
        recommendations = guardrails.filter_recommendations(recommendations)
        
        # Save recommendations to database
        from src.recommend.recommendation_engine import save_recommendations
        save_recommendations(user_id, recommendations)
        
        # Save persona assignment
        if persona_match:
            from src.personas.persona_classifier import save_persona_assignment
            save_persona_assignment(user_id, persona_match, window)
        
        # Format recommendations for response
        recs_data = [
            {
                "rec_id": rec.rec_id,
                "content_id": rec.content_id,
                "title": rec.title,
                "description": rec.description,
                "url": rec.url,
                "type": rec.type,
                "reading_time_minutes": rec.reading_time_minutes,
                "rationale": rec.rationale,
                "priority_score": rec.priority_score,
                "match_reasons": rec.match_reasons
            }
            for rec in recommendations
        ]
        
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"Generated {len(recommendations)} recommendations for {user_id} in {latency_ms:.0f}ms")
        
        return RecommendationResponse(
            user_id=user_id,
            recommendations=recs_data,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            persona=persona_match.persona_id if persona_match else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations/{rec_id}/approve")
async def approve_recommendation(rec_id: str, request: ApprovalRequest):
    """Approve or reject a recommendation.
    
    Args:
        rec_id: Recommendation identifier
        request: Approval request with approved flag and optional reason
    
    Returns:
        Success message
    """
    try:
        with database_transaction() as conn:
            # Check if recommendation exists
            result = conn.execute("""
                SELECT rec_id FROM recommendations WHERE rec_id = ?
            """, (rec_id,)).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Recommendation {rec_id} not found")
            
            # Update approval status
            conn.execute("""
                UPDATE recommendations 
                SET approved = ?, delivered = ?
                WHERE rec_id = ?
            """, (request.approved, request.approved, rec_id))
        
        action = "approved" if request.approved else "rejected"
        logger.info(f"Recommendation {rec_id} {action}")
        
        return {
            "rec_id": rec_id,
            "approved": request.approved,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving recommendation {rec_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/{rec_id}/view")
async def mark_recommendation_viewed(rec_id: str):
    """Mark a recommendation as viewed.
    
    Args:
        rec_id: Recommendation identifier
    
    Returns:
        Success message
    """
    try:
        from datetime import datetime
        
        with database_transaction() as conn:
            conn.execute("""
                UPDATE recommendations 
                SET viewed_at = ?
                WHERE rec_id = ?
            """, (datetime.now().isoformat(), rec_id))
        
        logger.info(f"Recommendation {rec_id} marked as viewed")
        
        return {
            "rec_id": rec_id,
            "status": "viewed",
            "viewed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error marking recommendation {rec_id} as viewed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

