"""
Tests for signal mapper
"""
import pytest
from src.features.schema import UserSignals
from src.recommend.signal_mapper import (
    map_signals_to_triggers, explain_triggers_for_user,
    validate_signal_mapping
)
from src.recommend.content_schema import SignalTrigger

class TestSignalMapper:
    """Test signal to trigger mapping."""
    
    def test_credit_utilization_threshold(self):
        """Test credit utilization threshold at exactly 0.5."""
        signals_above = UserSignals(credit_utilization_max=0.5, data_quality_score=0.9)
        signals_below = UserSignals(credit_utilization_max=0.49, data_quality_score=0.9)
        
        triggers_above = map_signals_to_triggers(signals_above)
        triggers_below = map_signals_to_triggers(signals_below)
        
        assert SignalTrigger.HIGH_CREDIT_UTILIZATION in triggers_above
        assert SignalTrigger.HIGH_CREDIT_UTILIZATION not in triggers_below
    
    def test_subscription_count_threshold(self):
        """Test subscription count threshold at exactly 3."""
        signals_at = UserSignals(subscription_count=3, data_quality_score=0.9)
        signals_below = UserSignals(subscription_count=2, data_quality_score=0.9)
        
        triggers_at = map_signals_to_triggers(signals_at)
        triggers_below = map_signals_to_triggers(signals_below)
        
        assert SignalTrigger.MANY_SUBSCRIPTIONS in triggers_at
        assert SignalTrigger.MANY_SUBSCRIPTIONS not in triggers_below
    
    def test_subscription_spend_threshold(self):
        """Test subscription spend threshold at exactly $50."""
        signals_at = UserSignals(monthly_subscription_spend=50.0, data_quality_score=0.9)
        signals_below = UserSignals(monthly_subscription_spend=49.99, data_quality_score=0.9)
        
        triggers_at = map_signals_to_triggers(signals_at)
        triggers_below = map_signals_to_triggers(signals_below)
        
        assert SignalTrigger.HIGH_SUBSCRIPTION_SPEND in triggers_at
        assert SignalTrigger.HIGH_SUBSCRIPTION_SPEND not in triggers_below
    
    def test_multiple_triggers(self):
        """Test that multiple triggers can be returned."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            has_interest_charges=True,
            subscription_count=5,
            monthly_subscription_spend=100.0,
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        
        assert len(triggers) >= 4
        assert SignalTrigger.HIGH_CREDIT_UTILIZATION in triggers
        assert SignalTrigger.HAS_INTEREST_CHARGES in triggers
        assert SignalTrigger.MANY_SUBSCRIPTIONS in triggers
        assert SignalTrigger.HIGH_SUBSCRIPTION_SPEND in triggers
    
    def test_insufficient_data_fallback(self):
        """Test that insufficient_data trigger is returned on error."""
        signals = UserSignals(insufficient_data=True, data_quality_score=0.9)
        triggers = map_signals_to_triggers(signals)
        assert SignalTrigger.INSUFFICIENT_DATA in triggers
    
    def test_none_values(self):
        """Test handling of None values in optional fields."""
        signals = UserSignals(
            credit_utilization_max=None,
            subscription_count=0,
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        assert SignalTrigger.HIGH_CREDIT_UTILIZATION not in triggers
    
    def test_all_credit_triggers(self):
        """Test all credit-related triggers."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            has_interest_charges=True,
            is_overdue=True,
            minimum_payment_only=True,
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        
        assert SignalTrigger.HIGH_CREDIT_UTILIZATION in triggers
        assert SignalTrigger.HAS_INTEREST_CHARGES in triggers
        assert SignalTrigger.IS_OVERDUE in triggers
        assert SignalTrigger.MINIMUM_PAYMENT_ONLY in triggers
    
    def test_income_triggers(self):
        """Test income-related triggers."""
        signals = UserSignals(
            income_pay_gap=50,  # > 45
            cash_flow_buffer=0.5,  # < 1.0
            income_variability=0.4,  # > 0.3
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        
        assert SignalTrigger.VARIABLE_INCOME in triggers
        assert SignalTrigger.LOW_CASH_BUFFER in triggers
        assert SignalTrigger.HIGH_INCOME_VARIABILITY in triggers
    
    def test_savings_triggers(self):
        """Test savings-related triggers."""
        signals = UserSignals(
            monthly_savings_inflow=250.0,  # > 0
            savings_growth_rate=-0.02,  # < 0
            emergency_fund_months=2.0,  # < 3.0
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        
        assert SignalTrigger.POSITIVE_SAVINGS in triggers
        assert SignalTrigger.NEGATIVE_SAVINGS_GROWTH in triggers
        assert SignalTrigger.LOW_EMERGENCY_FUND in triggers
    
    def test_bank_fee_triggers(self):
        """Test bank fee-related triggers."""
        signals = UserSignals(
            monthly_bank_fees=25.0,  # >= 20.0
            has_overdraft_fees=True,
            has_atm_fees=True,
            has_maintenance_fees=True,
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        
        assert SignalTrigger.HIGH_BANK_FEES in triggers
        assert SignalTrigger.HAS_OVERDRAFT_FEES in triggers
        assert SignalTrigger.HAS_ATM_FEES in triggers
        assert SignalTrigger.HAS_MAINTENANCE_FEES in triggers
    
    def test_bank_fee_threshold(self):
        """Test bank fee threshold at exactly $20."""
        signals_at = UserSignals(monthly_bank_fees=20.0, data_quality_score=0.9)
        signals_below = UserSignals(monthly_bank_fees=19.99, data_quality_score=0.9)
        
        triggers_at = map_signals_to_triggers(signals_at)
        triggers_below = map_signals_to_triggers(signals_below)
        
        assert SignalTrigger.HIGH_BANK_FEES in triggers_at
        assert SignalTrigger.HIGH_BANK_FEES not in triggers_below
    
    def test_bank_fee_boolean_triggers(self):
        """Test that boolean bank fee flags map correctly."""
        signals = UserSignals(
            monthly_bank_fees=15.0,  # Below threshold
            has_overdraft_fees=True,  # Should trigger
            has_atm_fees=False,
            has_maintenance_fees=False,
            data_quality_score=0.9
        )
        triggers = map_signals_to_triggers(signals)
        
        assert SignalTrigger.HIGH_BANK_FEES not in triggers  # Below $20
        assert SignalTrigger.HAS_OVERDRAFT_FEES in triggers
        assert SignalTrigger.HAS_ATM_FEES not in triggers
        assert SignalTrigger.HAS_MAINTENANCE_FEES not in triggers

class TestTriggerExplanations:
    """Test trigger explanation generation."""
    
    def test_explain_triggers(self):
        """Test that trigger explanations are generated."""
        triggers = [
            SignalTrigger.HIGH_CREDIT_UTILIZATION,
            SignalTrigger.MANY_SUBSCRIPTIONS
        ]
        explanations = explain_triggers_for_user(triggers)
        
        assert len(explanations) == 2
        assert "credit card utilization" in explanations[0].lower()
        assert "subscriptions" in explanations[1].lower()
    
    def test_validate_signal_mapping(self):
        """Test signal mapping validation."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            has_interest_charges=True,
            data_quality_score=0.9
        )
        is_valid = validate_signal_mapping(signals)
        assert is_valid is True

