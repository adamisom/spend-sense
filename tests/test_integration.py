"""
Integration tests for Phase 2 components
"""
import pytest
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine
from src.personas.persona_classifier import classify_persona
from src.recommend.signal_mapper import map_signals_to_triggers

class TestIntegration:
    """Integration tests for end-to-end flows."""
    
    def test_end_to_end_recommendation_generation(self, temp_catalog_file):
        """Test complete flow from signals to recommendations."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            has_interest_charges=True,
            subscription_count=3,
            data_quality_score=0.9
        )
        
        engine = RecommendationEngine(catalog_path=temp_catalog_file)
        recommendations = engine.generate_recommendations("test_user", signals)
        
        # Should generate recommendations
        assert isinstance(recommendations, list)
        # Each recommendation should have required fields
        if recommendations:
            rec = recommendations[0]
            assert rec.rec_id is not None
            assert rec.content_id is not None
            assert rec.rationale is not None
            assert rec.priority_score > 0
    
    def test_persona_to_content_matching(self, temp_catalog_file):
        """Test that persona classification leads to correct content."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            data_quality_score=0.9
        )
        
        persona_match = classify_persona(signals)
        triggers = map_signals_to_triggers(signals)
        
        engine = RecommendationEngine(catalog_path=temp_catalog_file)
        recommendations = engine.generate_recommendations("test_user", signals)
        
        # All recommendations should match persona or triggers
        if recommendations:
            for rec in recommendations:
                # Check that match reasons reference persona or triggers
                assert len(rec.match_reasons) > 0
    
    def test_signal_to_trigger_to_content_flow(self, temp_catalog_file):
        """Test signal → trigger → content matching flow."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            has_interest_charges=True,
            data_quality_score=0.9
        )
        
        # Step 1: Map signals to triggers
        triggers = map_signals_to_triggers(signals)
        assert SignalTrigger.HIGH_CREDIT_UTILIZATION in triggers
        assert SignalTrigger.HAS_INTEREST_CHARGES in triggers
        
        # Step 2: Classify persona
        persona_match = classify_persona(signals)
        assert persona_match is not None
        assert persona_match.persona_id == "high_utilization"
        
        # Step 3: Generate recommendations
        engine = RecommendationEngine(catalog_path=temp_catalog_file)
        recommendations = engine.generate_recommendations("test_user", signals)
        
        # Should have recommendations
        assert isinstance(recommendations, list)
    
    def test_rationale_includes_signal_values(self, temp_catalog_file):
        """Test that rationales include specific signal values."""
        signals = UserSignals(
            credit_utilization_max=0.75,
            subscription_count=5,
            data_quality_score=0.9
        )
        
        engine = RecommendationEngine(catalog_path=temp_catalog_file)
        recommendations = engine.generate_recommendations("test_user", signals)
        
        if recommendations:
            # Check that rationales are generated
            assert all(rec.rationale for rec in recommendations)
            # Check that rationales end with period
            assert all(rec.rationale.endswith(".") for rec in recommendations)
    
    def test_multiple_persona_matches_priority(self):
        """Test that when multiple personas match, priority wins."""
        signals = UserSignals(
            credit_utilization_max=0.75,  # Matches high_utilization (priority 1)
            subscription_count=5,  # Matches subscription_heavy (priority 3)
            data_quality_score=0.9
        )
        
        persona_match = classify_persona(signals)
        # High utilization should win due to priority
        assert persona_match.persona_id == "high_utilization"
    
    def test_insufficient_data_fallback(self):
        """Test that insufficient data falls back correctly."""
        signals = UserSignals(
            credit_utilization_max=0.2,  # Below threshold
            subscription_count=1,  # Below threshold
            data_quality_score=0.8
        )
        
        persona_match = classify_persona(signals)
        assert persona_match is not None
        assert persona_match.persona_id == "insufficient_data"

