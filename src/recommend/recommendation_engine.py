"""
Recommendation engine for SpendSense
Generates personalized content recommendations with explainable rationales
"""
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
from loguru import logger

from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona, PersonaMatch
from src.recommend.content_schema import (
    ContentCatalog, ContentItem, ContentType, SignalTrigger,
    load_content_catalog
)
from src.recommend.signal_mapper import map_signals_to_triggers, explain_triggers_for_user

@dataclass
class Recommendation:
    """A single recommendation with rationale."""
    rec_id: str
    content_id: str
    title: str
    description: str
    url: str
    type: str
    reading_time_minutes: int
    rationale: str  # "because" explanation
    priority_score: float
    match_reasons: List[str]  # Why this was recommended

class RecommendationEngine:
    """Main recommendation engine."""
    
    def __init__(self, catalog_path: str = "data/content/catalog.json"):
        """Initialize recommendation engine with content catalog."""
        self.catalog = load_content_catalog(catalog_path)
        logger.info(f"Recommendation engine initialized with {len(self.catalog.items)} content items")
    
    def generate_recommendations(
        self,
        user_id: str,
        signals: UserSignals,
        max_recommendations: int = 5,
        exclude_recent_days: int = 30
    ) -> List[Recommendation]:
        """Generate personalized recommendations for a user.
        
        Args:
            user_id: User identifier
            signals: Computed user signals
            max_recommendations: Maximum number of recommendations to return
            exclude_recent_days: Exclude content viewed in last N days
        
        Returns:
            List of Recommendation objects, sorted by priority
        """
        try:
            # Step 1: Classify persona
            persona_match = classify_persona(signals)
            if not persona_match:
                logger.warning(f"No persona match for user {user_id}")
                return []
            
            # Step 2: Map signals to triggers
            triggers = map_signals_to_triggers(signals)
            
            # Step 3: Get recently viewed content (for deduplication)
            recent_content_ids = self._get_recent_content_ids(user_id, exclude_recent_days)
            
            # Step 4: Filter and score content
            candidate_items = self._filter_content(persona_match, triggers)
            
            # Step 5: Check eligibility and deduplicate
            eligible_items = []
            for item in candidate_items:
                if item.content_id in recent_content_ids:
                    continue  # Skip recently viewed
                
                if self._check_eligibility(item, signals, user_id):
                    eligible_items.append(item)
            
            # Step 6: Score and rank
            scored_items = self._score_content(eligible_items, persona_match, triggers, signals)
            
            # Step 7: Generate recommendations with rationales
            recommendations = []
            for item, score in scored_items[:max_recommendations]:
                rationale = self._generate_rationale(item, persona_match, triggers, signals)
                match_reasons = self._get_match_reasons(item, persona_match, triggers)
                
                recommendations.append(Recommendation(
                    rec_id=str(uuid.uuid4()),
                    content_id=item.content_id,
                    title=item.title,
                    description=item.description,
                    url=item.url,
                    type=item.type.value,
                    reading_time_minutes=item.reading_time_minutes,
                    rationale=rationale,
                    priority_score=score,
                    match_reasons=match_reasons
                ))
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            return []
    
    def _filter_content(
        self,
        persona_match: PersonaMatch,
        triggers: List[SignalTrigger]
    ) -> List[ContentItem]:
        """Filter content by persona and signal triggers."""
        # Get content matching persona
        persona_items = self.catalog.get_by_personas([persona_match.persona_id])
        
        # Get content matching triggers
        trigger_items = self.catalog.get_by_signals(triggers)
        
        # Combine and deduplicate
        all_items = {item.content_id: item for item in persona_items + trigger_items}
        
        return list(all_items.values())
    
    def _check_eligibility(
        self,
        item: ContentItem,
        signals: UserSignals,
        user_id: str
    ) -> bool:
        """Check if user is eligible for this content item."""
        try:
            eligibility = item.eligibility
            
            # Check minimum income (would need user income data - skip for now)
            # if eligibility.min_income and user_income < eligibility.min_income:
            #     return False
            
            # Check minimum credit score (would need user credit score - skip for now)
            # if eligibility.min_credit_score and user_credit_score < eligibility.min_credit_score:
            #     return False
            
            # Check required account types (would need user account data - skip for now)
            # if eligibility.required_account_types:
            #     user_account_types = get_user_account_types(user_id)
            #     if not all(atype in user_account_types for atype in eligibility.required_account_types):
            #         return False
            
            # Check excluded products (would need user product data - skip for now)
            # if eligibility.excluded_products:
            #     user_products = get_user_products(user_id)
            #     if any(product in user_products for product in eligibility.excluded_products):
            #         return False
            
            # Check max age
            if eligibility.max_age_days:
                # Would need to check when content was created vs now
                # For now, assume all content is fresh
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking eligibility for {item.content_id}: {e}")
            return False
    
    def _score_content(
        self,
        items: List[ContentItem],
        persona_match: PersonaMatch,
        triggers: List[SignalTrigger],
        signals: UserSignals
    ) -> List[Tuple[ContentItem, float]]:
        """Score content items and return sorted list."""
        scored = []
        
        for item in items:
            score = item.priority_score  # Start with base priority
            
            # Boost if matches persona
            if persona_match.persona_id in item.personas:
                score += 2.0
            
            # Boost if matches triggers
            matching_triggers = [t for t in triggers if t in item.signal_triggers]
            score += len(matching_triggers) * 1.0
            
            # Boost for higher confidence persona match
            score += persona_match.confidence * 1.0
            
            # Prefer articles and checklists over calculators and partner offers
            if item.type == ContentType.ARTICLE:
                score += 0.5
            elif item.type == ContentType.CHECKLIST:
                score += 0.3
            elif item.type == ContentType.PARTNER_OFFER:
                score -= 0.5  # Slightly lower priority for partner offers
            
            scored.append((item, score))
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _generate_rationale(
        self,
        item: ContentItem,
        persona_match: PersonaMatch,
        triggers: List[SignalTrigger],
        signals: UserSignals
    ) -> str:
        """Generate human-readable rationale for recommendation."""
        reasons = []
        
        # Persona-based reason
        reasons.append(f"Based on your financial profile ({persona_match.persona_name.lower()})")
        
        # Trigger-based reasons
        matching_triggers = [t for t in triggers if t in item.signal_triggers]
        if matching_triggers:
            trigger_explanations = explain_triggers_for_user(matching_triggers)
            if trigger_explanations:
                reasons.append(f"because {trigger_explanations[0].lower()}")
        
        # Specific signal-based reasons
        if persona_match.persona_id == "high_utilization" and signals.credit_utilization_max:
            reasons.append(f"your credit utilization is {signals.credit_utilization_max*100:.0f}%")
        elif persona_match.persona_id == "subscription_heavy" and signals.subscription_count:
            reasons.append(f"you have {signals.subscription_count} active subscriptions")
        elif persona_match.persona_id == "variable_income" and signals.income_pay_gap:
            reasons.append(f"your income gaps are {signals.income_pay_gap} days apart")
        
        return ", ".join(reasons) + "."
    
    def _get_match_reasons(
        self,
        item: ContentItem,
        persona_match: PersonaMatch,
        triggers: List[SignalTrigger]
    ) -> List[str]:
        """Get list of reasons why this content matches."""
        reasons = []
        
        if persona_match.persona_id in item.personas:
            reasons.append(f"Matches {persona_match.persona_name} persona")
        
        matching_triggers = [t for t in triggers if t in item.signal_triggers]
        for trigger in matching_triggers:
            reasons.append(f"Matches {trigger.value} trigger")
        
        return reasons
    
    def _get_recent_content_ids(self, user_id: str, days: int) -> List[str]:
        """Get content IDs that user has viewed recently."""
        try:
            from src.db.connection import database_transaction
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with database_transaction() as conn:
                results = conn.execute("""
                    SELECT DISTINCT content_id 
                    FROM recommendations 
                    WHERE user_id = ? 
                    AND viewed_at IS NOT NULL 
                    AND viewed_at > ?
                """, (user_id, cutoff_date.isoformat())).fetchall()
            
            return [row['content_id'] for row in results]
            
        except Exception as e:
            logger.error(f"Error getting recent content IDs: {e}")
            return []

def save_recommendations(
    user_id: str,
    recommendations: List[Recommendation],
    db_path: str = "db/spend_sense.db"
) -> bool:
    """Save recommendations to database."""
    try:
        from src.db.connection import database_transaction
        
        with database_transaction(db_path) as conn:
            for rec in recommendations:
                conn.execute("""
                    INSERT INTO recommendations 
                    (rec_id, user_id, content_id, rationale, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    rec.rec_id,
                    user_id,
                    rec.content_id,
                    rec.rationale,
                    datetime.now().isoformat()
                ))
        
        logger.info(f"Saved {len(recommendations)} recommendations for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving recommendations: {e}")
        return False

