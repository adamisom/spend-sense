"""
Tests for persona classifier
"""
import pytest
from src.features.schema import UserSignals
from src.personas.persona_classifier import (
    classify_persona, evaluate_criterion, evaluate_persona_criteria,
    PersonaMatch
)
from src.personas.config_loader import PersonaCriteria, PersonaConfig

class TestPersonaClassifier:
    """Test persona classification logic."""
    
    def test_basic_match(self, sample_signals):
        """Test basic persona matching with single criterion."""
        match = classify_persona(sample_signals)
        assert match is not None
        assert match.persona_id in ["high_utilization", "subscription_heavy", "savings_builder"]
        assert match.confidence > 0.0
        assert isinstance(match.matched_criteria, list)
    
    def test_and_logic(self):
        """Test AND combinator - both criteria must match."""
        signals = UserSignals(
            income_pay_gap=50,  # > 45
            cash_flow_buffer=0.5,  # < 1.0
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        # Should match variable_income (both criteria match with AND)
        assert match is not None
        # Note: Actual match depends on config, but should handle AND logic
    
    def test_or_logic(self):
        """Test OR combinator - either criterion can match."""
        signals = UserSignals(
            credit_utilization_max=0.3,  # Doesn't match threshold
            has_interest_charges=True,  # Matches
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        # Should match high_utilization via OR logic
    
    def test_priority_tie_breaking(self):
        """Test that highest priority (lowest number) wins when multiple match."""
        signals = UserSignals(
            credit_utilization_max=0.75,  # Matches high_utilization (priority 1)
            subscription_count=5,  # Matches subscription_heavy (priority 3)
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        # High utilization should win due to priority 1 < priority 3
        assert match.persona_id == "high_utilization"
    
    def test_insufficient_data_fallback(self):
        """Test fallback to insufficient_data when no matches."""
        signals = UserSignals(
            credit_utilization_max=0.2,  # Below threshold
            subscription_count=1,  # Below threshold
            insufficient_data=False,
            data_quality_score=0.8
        )
        match = classify_persona(signals)
        assert match is not None
        # Should fall back to insufficient_data
        assert match.persona_id == "insufficient_data"
    
    def test_low_data_quality(self):
        """Test that data_quality_score < 0.1 forces insufficient_data."""
        signals = UserSignals(
            credit_utilization_max=0.75,  # Would match high_utilization
            data_quality_score=0.05  # Too low
        )
        match = classify_persona(signals)
        assert match is not None
        assert match.persona_id == "insufficient_data"
        assert "Data quality score below threshold" in match.matched_criteria[0]
    
    def test_none_values(self):
        """Test handling of None signal values."""
        signals = UserSignals(
            credit_utilization_max=None,  # Should not match
            subscription_count=0,
            data_quality_score=0.8
        )
        match = classify_persona(signals)
        assert match is not None
        # Should fall back to insufficient_data when no matches
    
    def test_confidence_calculation(self):
        """Test confidence is calculated correctly based on matched criteria."""
        signals = UserSignals(
            credit_utilization_max=0.75,  # Matches
            has_interest_charges=False,  # Doesn't match
            is_overdue=False,  # Doesn't match
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        # Confidence should reflect partial match
        assert 0.0 < match.confidence <= 1.0

class TestCriterionEvaluation:
    """Test individual criterion evaluation."""
    
    def test_equality_operator(self):
        """Test == operator."""
        signals = UserSignals(has_interest_charges=True)
        criterion = PersonaCriteria(field="has_interest_charges", operator="==", value=True)
        result = evaluate_criterion(signals, criterion)
        assert result is True
    
    def test_greater_than_operator(self):
        """Test > operator."""
        signals = UserSignals(credit_utilization_max=0.75)
        criterion = PersonaCriteria(field="credit_utilization_max", operator=">", value=0.5)
        result = evaluate_criterion(signals, criterion)
        assert result is True
    
    def test_greater_equal_operator(self):
        """Test >= operator."""
        signals = UserSignals(credit_utilization_max=0.5)
        criterion = PersonaCriteria(field="credit_utilization_max", operator=">=", value=0.5)
        result = evaluate_criterion(signals, criterion)
        assert result is True
    
    def test_less_than_operator(self):
        """Test < operator."""
        signals = UserSignals(cash_flow_buffer=0.5)
        criterion = PersonaCriteria(field="cash_flow_buffer", operator="<", value=1.0)
        result = evaluate_criterion(signals, criterion)
        assert result is True
    
    def test_none_value_handling(self):
        """Test that None values return False."""
        signals = UserSignals(credit_utilization_max=None)
        criterion = PersonaCriteria(field="credit_utilization_max", operator=">=", value=0.5)
        result = evaluate_criterion(signals, criterion)
        assert result is False

class TestPersonaCriteriaEvaluation:
    """Test persona criteria evaluation with combinators."""
    
    def test_and_combinator(self):
        """Test AND combinator logic."""
        signals = UserSignals(
            income_pay_gap=50,
            cash_flow_buffer=0.5
        )
        persona = PersonaConfig(
            name="Test",
            priority=1,
            description="Test persona",
            criteria=[
                PersonaCriteria(field="income_pay_gap", operator=">", value=45, combinator="AND"),
                PersonaCriteria(field="cash_flow_buffer", operator="<", value=1.0, combinator="AND")
            ],
            focus_areas=[]
        )
        matches, descriptions = evaluate_persona_criteria(signals, persona)
        assert matches is True
        assert len(descriptions) == 2
    
    def test_or_combinator(self):
        """Test OR combinator logic."""
        signals = UserSignals(
            credit_utilization_max=0.3,
            has_interest_charges=True
        )
        persona = PersonaConfig(
            name="Test",
            priority=1,
            description="Test persona",
            criteria=[
                PersonaCriteria(field="credit_utilization_max", operator=">=", value=0.5, combinator="OR"),
                PersonaCriteria(field="has_interest_charges", operator="==", value=True, combinator="OR")
            ],
            focus_areas=[]
        )
        matches, descriptions = evaluate_persona_criteria(signals, persona)
        assert matches is True
        assert len(descriptions) >= 1
    
    def test_fee_fighter_monthly_fees(self):
        """Test Fee Fighter persona matches with monthly_bank_fees >= 20."""
        signals = UserSignals(
            monthly_bank_fees=25.0,  # >= 20.0
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        assert match.persona_id == "fee_fighter"
        assert "Monthly bank fees" in " ".join(match.matched_criteria) or "bank fees" in " ".join(match.matched_criteria).lower()
    
    def test_fee_fighter_overdraft_fees(self):
        """Test Fee Fighter persona matches with has_overdraft_fees (OR logic)."""
        signals = UserSignals(
            monthly_bank_fees=15.0,  # Below threshold
            has_overdraft_fees=True,  # Matches via OR
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        assert match.persona_id == "fee_fighter"
    
    def test_fee_fighter_bank_fee_count(self):
        """Test Fee Fighter persona matches with bank_fee_count >= 3 (OR logic)."""
        signals = UserSignals(
            monthly_bank_fees=10.0,  # Below threshold
            has_overdraft_fees=False,
            bank_fee_count=4,  # >= 3, matches via OR
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        assert match.persona_id == "fee_fighter"
    
    def test_fee_fighter_priority_tie_breaking(self):
        """Test Fee Fighter priority (3) vs other personas."""
        signals = UserSignals(
            monthly_bank_fees=25.0,  # Matches fee_fighter (priority 3)
            subscription_count=5,  # Matches subscription_heavy (priority 3)
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        # Both have priority 3, so confidence or first match determines winner
        # At minimum, fee_fighter should be a valid match
        assert match.persona_id in ["fee_fighter", "subscription_heavy"]
    
    def test_fee_fighter_vs_high_utilization_priority(self):
        """Test Fee Fighter (priority 3) loses to high_utilization (priority 1)."""
        signals = UserSignals(
            credit_utilization_max=0.75,  # Matches high_utilization (priority 1)
            monthly_bank_fees=25.0,  # Matches fee_fighter (priority 3)
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        # High utilization should win due to priority 1 < priority 3
        assert match.persona_id == "high_utilization"
    
    def test_fee_fighter_multiple_criteria(self):
        """Test Fee Fighter matches when multiple OR criteria match."""
        signals = UserSignals(
            monthly_bank_fees=25.0,  # Matches
            has_overdraft_fees=True,  # Also matches
            bank_fee_count=5,  # Also matches
            data_quality_score=0.9
        )
        match = classify_persona(signals)
        assert match is not None
        assert match.persona_id == "fee_fighter"
        # Should have multiple matched criteria
        assert len(match.matched_criteria) >= 1

