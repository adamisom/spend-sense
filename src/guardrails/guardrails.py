"""
Guardrails for SpendSense recommendations
Ensures safe, appropriate, and compliant content delivery
"""
import re
from typing import List, Optional, Dict, Any
from loguru import logger

from src.recommend.content_schema import ContentItem
from src.recommend.recommendation_engine import Recommendation

class GuardrailViolation(Exception):
    """Raised when a guardrail is violated."""
    def __init__(self, guardrail_name: str, reason: str):
        self.guardrail_name = guardrail_name
        self.reason = reason
        super().__init__(f"Guardrail violation: {guardrail_name} - {reason}")

class Guardrails:
    """Guardrails for recommendation safety and compliance."""
    
    # Prohibited patterns (financial shaming, negative language)
    PROHIBITED_PATTERNS = [
        r'\b(you\'re|you are) (stupid|dumb|idiot|fool|waste|terrible|awful)\b',
        r'\b(always|never) (spend|waste|throw away)\b',
        r'\b(pathetic|worthless|loser)\b',
        r'\b(you deserve|you earned) (this|it)\b.*\b(debt|trouble|problem)\b',
    ]
    
    # Required disclaimers by content type
    DISCLAIMERS = {
        "partner_offer": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.",
        "calculator": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.",
        "article": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.",
        "checklist": "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
    }
    
    def __init__(self):
        """Initialize guardrails."""
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.PROHIBITED_PATTERNS]
        logger.info("Guardrails initialized")
    
    def check_consent(self, user_id: str) -> bool:
        """Check if user has consented to recommendations.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if user has consented, False otherwise
        
        Raises:
            GuardrailViolation if consent check fails
        """
        try:
            from src.db.connection import database_transaction
            
            with database_transaction() as conn:
                result = conn.execute("""
                    SELECT consent_status FROM users WHERE user_id = ?
                """, (user_id,)).fetchone()
                
                if not result:
                    raise GuardrailViolation(
                        "consent_check",
                        f"User {user_id} not found in database"
                    )
                
                if not result['consent_status']:
                    raise GuardrailViolation(
                        "consent_check",
                        f"User {user_id} has not consented to recommendations"
                    )
                
                return True
                
        except GuardrailViolation:
            raise
        except Exception as e:
            logger.error(f"Error checking consent: {e}")
            raise GuardrailViolation("consent_check", f"Error checking consent: {e}")
    
    def validate_content_safety(self, content: ContentItem) -> bool:
        """Validate that content doesn't contain prohibited patterns.
        
        Args:
            content: ContentItem to validate
        
        Returns:
            True if content is safe
        
        Raises:
            GuardrailViolation if content contains prohibited patterns
        """
        text_to_check = f"{content.title} {content.description}".lower()
        
        for pattern in self.compiled_patterns:
            if pattern.search(text_to_check):
                raise GuardrailViolation(
                    "content_safety",
                    f"Content {content.content_id} contains prohibited pattern"
                )
        
        return True
    
    def enforce_positive_framing(self, text: str) -> str:
        """Enforce positive framing in text.
        
        Args:
            text: Text to check and potentially rewrite
        
        Returns:
            Text with positive framing enforced
        """
        # Simple positive framing rules
        replacements = {
            r'\b(can\'t|cannot) (afford|pay|manage)\b': "can work toward",
            r'\b(too (much|many|high|low))\b': "opportunity to optimize",
            r'\b(failure|failed|failing)\b': "learning opportunity",
            r'\b(problem|issue|trouble)\b': "area for improvement",
        }
        
        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def inject_disclaimer(self, content: ContentItem, rationale: str) -> str:
        """Inject required disclaimer into rationale.
        
        Args:
            content: ContentItem
            rationale: Original rationale
        
        Returns:
            Rationale with disclaimer appended
        """
        disclaimer = self.DISCLAIMERS.get(content.type.value, self.DISCLAIMERS["article"])
        return f"{rationale} {disclaimer}"
    
    def validate_recommendation(self, recommendation: Recommendation) -> bool:
        """Validate a complete recommendation.
        
        Args:
            recommendation: Recommendation to validate
        
        Returns:
            True if recommendation passes all guardrails
        
        Raises:
            GuardrailViolation if validation fails
        """
        # Check rationale for prohibited patterns
        rationale_lower = recommendation.rationale.lower()
        for pattern in self.compiled_patterns:
            if pattern.search(rationale_lower):
                raise GuardrailViolation(
                    "recommendation_safety",
                    f"Recommendation {recommendation.rec_id} rationale contains prohibited pattern"
                )
        
        # Ensure disclaimer is present for partner offers
        if recommendation.type == "partner_offer":
            if "disclaimer" not in recommendation.rationale.lower():
                logger.warning(f"Partner offer {recommendation.rec_id} missing disclaimer")
        
        return True
    
    def filter_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Filter recommendations through guardrails.
        
        Args:
            recommendations: List of recommendations to filter
        
        Returns:
            Filtered list of recommendations that pass guardrails
        """
        filtered = []
        
        for rec in recommendations:
            try:
                # Validate recommendation
                self.validate_recommendation(rec)
                
                # Enforce positive framing
                rec.rationale = self.enforce_positive_framing(rec.rationale)
                
                # Inject disclaimer if needed
                # Note: We'd need ContentItem here, but we have type
                if rec.type == "partner_offer":
                    disclaimer = self.DISCLAIMERS["partner_offer"]
                    if disclaimer.lower() not in rec.rationale.lower():
                        rec.rationale = f"{rec.rationale} {disclaimer}"
                
                filtered.append(rec)
                
            except GuardrailViolation as e:
                logger.warning(f"Recommendation {rec.rec_id} filtered out: {e.reason}")
                continue
            except Exception as e:
                logger.error(f"Error filtering recommendation {rec.rec_id}: {e}")
                continue
        
        logger.info(f"Filtered {len(recommendations)} recommendations to {len(filtered)} safe recommendations")
        return filtered
    
    def check_rate_limit(self, user_id: str, max_per_day: int = 10) -> bool:
        """Check if user has exceeded recommendation rate limit.
        
        Args:
            user_id: User identifier
            max_per_day: Maximum recommendations per day
        
        Returns:
            True if within rate limit, False if exceeded
        
        Raises:
            GuardrailViolation if rate limit exceeded
        """
        try:
            from src.db.connection import database_transaction
            from datetime import datetime, timedelta
            
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            with database_transaction() as conn:
                count = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM recommendations
                    WHERE user_id = ? AND created_at >= ?
                """, (user_id, today_start.isoformat())).fetchone()
                
                if count and count['count'] >= max_per_day:
                    raise GuardrailViolation(
                        "rate_limit",
                        f"User {user_id} has exceeded daily recommendation limit ({max_per_day})"
                    )
                
                return True
                
        except GuardrailViolation:
            raise
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Don't block on rate limit check errors
            return True

# Global guardrails instance
guardrails = Guardrails()

