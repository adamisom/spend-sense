"""
Map user signals to content triggers
CRITICAL: Bridges numeric signals to categorical content matching
"""
from typing import List, Dict, Any
from src.features.schema import UserSignals
from src.recommend.content_schema import SignalTrigger
from loguru import logger

def map_signals_to_triggers(signals: UserSignals) -> List[SignalTrigger]:
    """Convert numeric user signals to categorical content triggers.
    
    This is the critical bridge between signal detection and content recommendation.
    """
    triggers = []
    
    try:
        # Credit-related triggers
        if signals.credit_utilization_max is not None and signals.credit_utilization_max >= 0.5:
            triggers.append(SignalTrigger.HIGH_CREDIT_UTILIZATION)
        
        if signals.has_interest_charges:
            triggers.append(SignalTrigger.HAS_INTEREST_CHARGES)
        
        if signals.is_overdue:
            triggers.append(SignalTrigger.IS_OVERDUE)
        
        if signals.minimum_payment_only:
            triggers.append(SignalTrigger.MINIMUM_PAYMENT_ONLY)
        
        # Income-related triggers
        if signals.income_pay_gap is not None and signals.income_pay_gap > 45:
            triggers.append(SignalTrigger.VARIABLE_INCOME)
        
        if signals.cash_flow_buffer is not None and signals.cash_flow_buffer < 1.0:
            triggers.append(SignalTrigger.LOW_CASH_BUFFER)
        
        if signals.income_variability is not None and signals.income_variability > 0.3:
            triggers.append(SignalTrigger.HIGH_INCOME_VARIABILITY)
        
        # Subscription-related triggers
        if signals.subscription_count >= 3:
            triggers.append(SignalTrigger.MANY_SUBSCRIPTIONS)
        
        if signals.monthly_subscription_spend >= 50.0:
            triggers.append(SignalTrigger.HIGH_SUBSCRIPTION_SPEND)
        
        if signals.subscription_share >= 0.10:
            triggers.append(SignalTrigger.HIGH_SUBSCRIPTION_SHARE)
        
        # Savings-related triggers
        if signals.monthly_savings_inflow > 0:
            triggers.append(SignalTrigger.POSITIVE_SAVINGS)
        
        if signals.savings_growth_rate is not None and signals.savings_growth_rate < 0:
            triggers.append(SignalTrigger.NEGATIVE_SAVINGS_GROWTH)
        
        if signals.emergency_fund_months is not None and signals.emergency_fund_months < 3.0:
            triggers.append(SignalTrigger.LOW_EMERGENCY_FUND)
        
        # Bank fee triggers (NEW)
        if signals.monthly_bank_fees >= 20.0:
            triggers.append(SignalTrigger.HIGH_BANK_FEES)
        if signals.has_overdraft_fees:
            triggers.append(SignalTrigger.HAS_OVERDRAFT_FEES)
        if signals.has_atm_fees:
            triggers.append(SignalTrigger.HAS_ATM_FEES)
        if signals.has_maintenance_fees:
            triggers.append(SignalTrigger.HAS_MAINTENANCE_FEES)
        
        # Data quality triggers
        if signals.insufficient_data:
            triggers.append(SignalTrigger.INSUFFICIENT_DATA)
        
        logger.debug(f"Mapped {len(triggers)} triggers from signals: {[t.value for t in triggers]}")
        return triggers
        
    except Exception as e:
        logger.error(f"Error mapping signals to triggers: {e}")
        # Return at least insufficient data trigger as fallback
        return [SignalTrigger.INSUFFICIENT_DATA]

def get_trigger_explanations() -> Dict[SignalTrigger, str]:
    """Get human-readable explanations for each trigger."""
    return {
        # Credit explanations
        SignalTrigger.HIGH_CREDIT_UTILIZATION: "Your credit card utilization is above 50%",
        SignalTrigger.HAS_INTEREST_CHARGES: "You're paying interest charges on credit cards",
        SignalTrigger.IS_OVERDUE: "You have overdue payments",
        SignalTrigger.MINIMUM_PAYMENT_ONLY: "You're making minimum payments only",
        
        # Income explanations
        SignalTrigger.VARIABLE_INCOME: "Your income timing is irregular (gaps over 45 days)",
        SignalTrigger.LOW_CASH_BUFFER: "Your cash flow buffer is less than 1 month of expenses",
        SignalTrigger.HIGH_INCOME_VARIABILITY: "Your income amounts vary significantly",
        
        # Subscription explanations
        SignalTrigger.MANY_SUBSCRIPTIONS: "You have 3 or more active subscriptions",
        SignalTrigger.HIGH_SUBSCRIPTION_SPEND: "You spend $50+ monthly on subscriptions",
        SignalTrigger.HIGH_SUBSCRIPTION_SHARE: "Subscriptions are 10%+ of your total spending",
        
        # Savings explanations
        SignalTrigger.POSITIVE_SAVINGS: "You're actively saving money",
        SignalTrigger.NEGATIVE_SAVINGS_GROWTH: "Your savings balance is decreasing",
        SignalTrigger.LOW_EMERGENCY_FUND: "Your emergency fund covers less than 3 months of expenses",
        
        # Bank fee explanations
        SignalTrigger.HIGH_BANK_FEES: "You're paying $20+ monthly in bank fees",
        SignalTrigger.HAS_OVERDRAFT_FEES: "You've been charged overdraft fees",
        SignalTrigger.HAS_ATM_FEES: "You're paying ATM fees",
        SignalTrigger.HAS_MAINTENANCE_FEES: "You're paying account maintenance fees",
        
        # Data quality explanations
        SignalTrigger.INSUFFICIENT_DATA: "We need more transaction data to provide personalized recommendations"
    }

def explain_triggers_for_user(triggers: List[SignalTrigger]) -> List[str]:
    """Generate human-readable explanations for a user's triggers."""
    explanations = get_trigger_explanations()
    return [explanations.get(trigger, f"Trigger: {trigger.value}") for trigger in triggers]

# Testing and validation functions
def validate_signal_mapping(test_signals: UserSignals) -> bool:
    """Validate that signal mapping produces expected triggers."""
    try:
        triggers = map_signals_to_triggers(test_signals)
        
        # Should always return at least one trigger
        if not triggers:
            logger.error("Signal mapping returned no triggers")
            return False
        
        # Should return insufficient_data trigger if data quality is poor
        if test_signals.insufficient_data and SignalTrigger.INSUFFICIENT_DATA not in triggers:
            logger.error("Should return insufficient_data trigger for poor quality signals")
            return False
        
        # Should return appropriate credit triggers
        if (test_signals.credit_utilization_max and test_signals.credit_utilization_max >= 0.5 
            and SignalTrigger.HIGH_CREDIT_UTILIZATION not in triggers):
            logger.error("Should return high_credit_utilization trigger")
            return False
        
        logger.info(f"Signal mapping validation passed: {len(triggers)} triggers")
        return True
        
    except Exception as e:
        logger.error(f"Signal mapping validation failed: {e}")
        return False

# Batch processing for multiple users
def map_signals_batch(signals_dict: Dict[str, UserSignals]) -> Dict[str, List[SignalTrigger]]:
    """Map signals to triggers for multiple users."""
    results = {}
    for user_id, signals in signals_dict.items():
        results[user_id] = map_signals_to_triggers(signals)
    return results

