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
            from src.guardrails.guardrails import Guardrails
            guardrails = Guardrails()
            
            recommendations = []
            for item, score in scored_items[:max_recommendations]:
                rationale = self._generate_rationale(item, persona_match, triggers, signals)
                
                # Inject disclaimer based on content type
                rationale = guardrails.inject_disclaimer(item, rationale)
                
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
        """Generate human-readable rationale for recommendation.
        
        Only mentions signals relevant to the content item's triggers,
        ensuring the explanation is tailored and relevant.
        """
        import random
        
        # Get matching triggers for this specific content item
        matching_triggers = [t for t in triggers if t in item.signal_triggers]
        
        if not matching_triggers:
            # Fallback if no triggers match
            return f"This content matches your {persona_match.persona_name.lower()} financial profile."
        
        # Build rationale based on content-specific triggers only
        rationale_parts = []
        
        # Map triggers to specific signal values and natural phrasing
        trigger_details = []
        
        for trigger in matching_triggers:
            detail = self._get_trigger_detail(trigger, signals)
            if detail:
                trigger_details.append(detail)
        
        if not trigger_details:
            # Fallback if no details available
            trigger_explanations = explain_triggers_for_user(matching_triggers)
            if trigger_explanations:
                return f"This is relevant because {trigger_explanations[0].lower()}."
            return f"This content matches your {persona_match.persona_name.lower()} financial profile."
        
        # Create natural, varied rationales
        opening_phrases = [
            "This is relevant",
            "This matters",
            "This is important",
            "This can help",
            "This applies to you"
        ]
        
        opening = random.choice(opening_phrases)
        
        # Use the most specific detail available
        primary_detail = trigger_details[0]
        
        # Create natural sentence structure
        if len(trigger_details) == 1:
            rationale = f"{opening} because {primary_detail}."
        else:
            # If multiple relevant signals, mention the primary one
            rationale = f"{opening} because {primary_detail}."
        
        return rationale
    
    def _get_trigger_detail(self, trigger: SignalTrigger, signals: UserSignals) -> Optional[str]:
        """Get specific, natural-language detail for a trigger based on actual signal values."""
        from src.recommend.content_schema import SignalTrigger
        
        # Credit-related triggers
        if trigger == SignalTrigger.HIGH_CREDIT_UTILIZATION:
            if signals.credit_utilization_max is not None:
                util_pct = signals.credit_utilization_max * 100
                if util_pct >= 80:
                    return f"your credit utilization is {util_pct:.0f}% (well above the recommended 30%)"
                elif util_pct >= 50:
                    return f"your credit utilization is {util_pct:.0f}% (above the recommended 30%)"
                else:
                    return f"your credit utilization is {util_pct:.0f}%"
        
        elif trigger == SignalTrigger.HAS_INTEREST_CHARGES:
            if signals.credit_utilization_max is not None:
                return f"you're paying interest charges on {signals.credit_utilization_max*100:.0f}% credit utilization"
            return "you're paying interest charges on your credit cards"
        
        elif trigger == SignalTrigger.IS_OVERDUE:
            return "you have overdue payments that need attention"
        
        elif trigger == SignalTrigger.MINIMUM_PAYMENT_ONLY:
            return "you're making only minimum payments, which extends your debt timeline"
        
        # Subscription-related triggers
        elif trigger == SignalTrigger.MANY_SUBSCRIPTIONS:
            if signals.subscription_count:
                return f"you have {signals.subscription_count} active subscriptions"
            return "you have multiple active subscriptions"
        
        elif trigger == SignalTrigger.HIGH_SUBSCRIPTION_SPEND:
            if signals.monthly_subscription_spend:
                spend = signals.monthly_subscription_spend
                if spend >= 100:
                    return f"you're spending ${spend:.0f}+ per month on subscriptions"
                else:
                    return f"you're spending ${spend:.0f} per month on subscriptions"
            return "you're spending $50+ per month on subscriptions"
        
        elif trigger == SignalTrigger.HIGH_SUBSCRIPTION_SHARE:
            if signals.subscription_share:
                share_pct = signals.subscription_share * 100
                return f"subscriptions make up {share_pct:.0f}% of your total spending"
            return "subscriptions make up a significant portion of your spending"
        
        # Income-related triggers
        elif trigger == SignalTrigger.VARIABLE_INCOME:
            if signals.income_pay_gap:
                return f"your income arrives irregularly, with gaps of {signals.income_pay_gap} days between payments"
            return "your income timing is irregular"
        
        elif trigger == SignalTrigger.LOW_CASH_BUFFER:
            if signals.cash_flow_buffer is not None:
                if signals.cash_flow_buffer < 0.5:
                    return f"you have less than {signals.cash_flow_buffer*30:.0f} days of expenses saved"
                return f"your cash buffer is less than 1 month of expenses"
            return "your cash flow buffer is low"
        
        elif trigger == SignalTrigger.HIGH_INCOME_VARIABILITY:
            if signals.income_variability:
                var_pct = signals.income_variability * 100
                return f"your income varies by {var_pct:.0f}% month to month"
            return "your income amounts vary significantly"
        
        # Savings-related triggers
        elif trigger == SignalTrigger.POSITIVE_SAVINGS:
            if signals.monthly_savings_inflow:
                return f"you're saving ${signals.monthly_savings_inflow:.0f} per month"
            return "you're actively saving money"
        
        elif trigger == SignalTrigger.LOW_EMERGENCY_FUND:
            if signals.emergency_fund_months is not None:
                if signals.emergency_fund_months < 1:
                    return f"your emergency fund covers less than 1 month of expenses"
                return f"your emergency fund covers {signals.emergency_fund_months:.1f} months of expenses (recommended: 3-6 months)"
            return "your emergency fund is below recommended levels"
        
        elif trigger == SignalTrigger.NEGATIVE_SAVINGS_GROWTH:
            return "your savings balance is decreasing over time"
        
        # Bank fee triggers
        elif trigger == SignalTrigger.HIGH_BANK_FEES:
            if signals.monthly_bank_fees:
                return f"you're paying ${signals.monthly_bank_fees:.0f} per month in bank fees"
            return "you're paying $20+ per month in bank fees"
        
        elif trigger == SignalTrigger.HAS_OVERDRAFT_FEES:
            return "you've been charged overdraft fees recently"
        
        elif trigger == SignalTrigger.HAS_ATM_FEES:
            return "you're paying ATM fees when withdrawing cash"
        
        elif trigger == SignalTrigger.HAS_MAINTENANCE_FEES:
            return "you're paying account maintenance fees"
        
        # Fraud triggers
        elif trigger == SignalTrigger.HAS_FRAUD_HISTORY:
            if signals.fraud_transaction_count:
                return f"you've had {signals.fraud_transaction_count} fraud transaction{'s' if signals.fraud_transaction_count > 1 else ''} in your account"
            return "you have fraud transactions in your account history"
        
        elif trigger == SignalTrigger.HIGH_FRAUD_RISK:
            if signals.fraud_risk_score:
                risk_pct = signals.fraud_risk_score * 100
                return f"your account shows a {risk_pct:.0f}% fraud risk score"
            return "your account shows elevated fraud risk"
        
        elif trigger == SignalTrigger.ELEVATED_FRAUD_RATE:
            if signals.fraud_rate:
                rate_pct = signals.fraud_rate * 100
                return f"{rate_pct:.1f}% of your transactions are flagged as fraud"
            return "your fraud rate is above normal levels"
        
        # Data quality
        elif trigger == SignalTrigger.INSUFFICIENT_DATA:
            return "we need more transaction data to provide personalized recommendations"
        
        return None
    
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

