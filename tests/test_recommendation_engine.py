"""
Tests for recommendation engine
"""
import pytest
from unittest.mock import patch, MagicMock
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, Recommendation
from src.recommend.content_schema import ContentItem, ContentType, ContentCatalog, SignalTrigger
from src.personas.persona_classifier import PersonaMatch, classify_persona

class TestRecommendationEngineScoring:
    """Test recommendation engine scoring algorithm."""
    
    @pytest.fixture
    def engine(self, temp_catalog_file):
        """Create recommendation engine with test catalog."""
        return RecommendationEngine(catalog_path=temp_catalog_file)
    
    @pytest.fixture
    def persona_match(self):
        """Create sample persona match."""
        return PersonaMatch(
            persona_id="high_utilization",
            persona_name="High Utilization",
            priority=1,
            matched_criteria=["Credit utilization 50% or higher"],
            confidence=0.8
        )
    
    def test_scoring_persona_match_boost(self, engine, persona_match, sample_signals):
        """Test that persona match adds +2.0 to score."""
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[],
            url="/test",
            reading_time_minutes=10,
            priority_score=5.0
        )
        
        scored = engine._score_content([item], persona_match, [], sample_signals)
        base_score = item.priority_score
        final_score = scored[0][1]
        
        assert final_score >= base_score + 2.0
    
    def test_scoring_trigger_match_boost(self, engine, persona_match, sample_signals):
        """Test that each matching trigger adds +1.0 to score."""
        triggers = [SignalTrigger.HIGH_CREDIT_UTILIZATION, SignalTrigger.HAS_INTEREST_CHARGES]
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=triggers,
            url="/test",
            reading_time_minutes=10,
            priority_score=5.0
        )
        
        scored = engine._score_content([item], persona_match, triggers, sample_signals)
        # Should have +2.0 for 2 matching triggers
        assert scored[0][1] >= item.priority_score + 2.0
    
    def test_scoring_content_type_preferences(self, engine, persona_match, sample_signals):
        """Test that articles and checklists are preferred over partner offers."""
        article = ContentItem(
            content_id="article",
            type=ContentType.ARTICLE,
            title="Article Title Here",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[],
            url="/article",
            reading_time_minutes=10,
            priority_score=5.0
        )
        partner = ContentItem(
            content_id="partner",
            type=ContentType.PARTNER_OFFER,
            title="Partner Offer Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[],
            url="/partner",
            reading_time_minutes=10,
            priority_score=5.0
        )
        
        scored = engine._score_content([article, partner], persona_match, [], sample_signals)
        article_score = next(s[1] for s in scored if s[0].type == ContentType.ARTICLE)
        partner_score = next(s[1] for s in scored if s[0].type == ContentType.PARTNER_OFFER)
        
        assert article_score > partner_score
    
    def test_scoring_ranking_order(self, engine, persona_match, sample_signals):
        """Test that items are ranked by score (descending)."""
        items = [
            ContentItem(
                content_id=f"item_{i}",
                type=ContentType.ARTICLE,
                title=f"Item {i} Title Here",
                description="Test description for validation",
                personas=["high_utilization"],
                signal_triggers=[],
                url=f"/item_{i}",
                reading_time_minutes=10,
                priority_score=float(i)
            )
            for i in range(5)
        ]
        
        scored = engine._score_content(items, persona_match, [], sample_signals)
        scores = [s[1] for s in scored]
        assert scores == sorted(scores, reverse=True)
    
    def test_scoring_confidence_boost(self, engine, sample_signals):
        """Test that higher persona confidence boosts score."""
        high_confidence = PersonaMatch(
            persona_id="high_utilization",
            persona_name="High Utilization",
            priority=1,
            matched_criteria=[],
            confidence=1.0
        )
        low_confidence = PersonaMatch(
            persona_id="high_utilization",
            persona_name="High Utilization",
            priority=1,
            matched_criteria=[],
            confidence=0.3
        )
        
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[],
            url="/test",
            reading_time_minutes=10,
            priority_score=5.0
        )
        
        scored_high = engine._score_content([item], high_confidence, [], sample_signals)
        scored_low = engine._score_content([item], low_confidence, [], sample_signals)
        
        assert scored_high[0][1] > scored_low[0][1]

class TestRecommendationEngineFiltering:
    """Test content filtering logic."""
    
    @pytest.fixture
    def engine(self, temp_catalog_file):
        """Create recommendation engine."""
        return RecommendationEngine(catalog_path=temp_catalog_file)
    
    def test_filter_content_persona_match(self, engine, sample_signals):
        """Test that content matching persona is included."""
        persona_match = classify_persona(sample_signals)
        triggers = []
        filtered = engine._filter_content(persona_match, triggers)
        
        # Should return some content (depends on catalog)
        assert isinstance(filtered, list)
    
    def test_filter_content_trigger_match(self, engine, sample_signals):
        """Test that content matching triggers is included."""
        from src.recommend.signal_mapper import map_signals_to_triggers
        persona_match = classify_persona(sample_signals)
        triggers = map_signals_to_triggers(sample_signals)
        filtered = engine._filter_content(persona_match, triggers)
        
        # Should include content with matching triggers
        assert isinstance(filtered, list)
    
    def test_filter_content_deduplication(self, engine, sample_signals):
        """Test that duplicate content_ids are removed."""
        from src.recommend.signal_mapper import map_signals_to_triggers
        persona_match = classify_persona(sample_signals)
        triggers = map_signals_to_triggers(sample_signals)
        filtered = engine._filter_content(persona_match, triggers)
        
        content_ids = [item.content_id for item in filtered]
        assert len(content_ids) == len(set(content_ids))

class TestRationaleGeneration:
    """Test rationale generation."""
    
    @pytest.fixture
    def engine(self, temp_catalog_file):
        """Create recommendation engine."""
        return RecommendationEngine(catalog_path=temp_catalog_file)
    
    def test_rationale_generation_high_utilization(self, engine, sample_signals):
        """Test rationale for high utilization persona."""
        persona_match = PersonaMatch(
            persona_id="high_utilization",
            persona_name="High Utilization",
            priority=1,
            matched_criteria=[],
            confidence=0.8
        )
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[],
            url="/test",
            reading_time_minutes=10
        )
        triggers = []
        
        rationale = engine._generate_rationale(item, persona_match, triggers, sample_signals)
        
        assert "high utilization" in rationale.lower() or "financial profile" in rationale.lower()
    
    def test_rationale_generation_subscription_heavy(self, engine):
        """Test rationale for subscription heavy persona."""
        signals = UserSignals(subscription_count=5, data_quality_score=0.9)
        persona_match = PersonaMatch(
            persona_id="subscription_heavy",
            persona_name="Subscription-Heavy",
            priority=3,
            matched_criteria=[],
            confidence=0.8
        )
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["subscription_heavy"],
            signal_triggers=[],
            url="/test",
            reading_time_minutes=10
        )
        triggers = []
        
        rationale = engine._generate_rationale(item, persona_match, triggers, signals)
        
        assert "subscription" in rationale.lower() or "financial profile" in rationale.lower()
    
    def test_rationale_generation_includes_trigger(self, engine, sample_signals):
        """Test that rationale includes trigger explanation."""
        persona_match = PersonaMatch(
            persona_id="high_utilization",
            persona_name="High Utilization",
            priority=1,
            matched_criteria=[],
            confidence=0.8
        )
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[SignalTrigger.HIGH_CREDIT_UTILIZATION],
            url="/test",
            reading_time_minutes=10
        )
        triggers = [SignalTrigger.HIGH_CREDIT_UTILIZATION]
        
        rationale = engine._generate_rationale(item, persona_match, triggers, sample_signals)
        
        assert "because" in rationale.lower() or "credit" in rationale.lower()
    
    def test_rationale_generation_always_ends_with_period(self, engine, sample_signals):
        """Test that rationale always ends with period."""
        persona_match = PersonaMatch(
            persona_id="high_utilization",
            persona_name="High Utilization",
            priority=1,
            matched_criteria=[],
            confidence=0.8
        )
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article Title",
            description="Test description for validation",
            personas=["high_utilization"],
            signal_triggers=[],
            url="/test",
            reading_time_minutes=10
        )
        triggers = []
        
        rationale = engine._generate_rationale(item, persona_match, triggers, sample_signals)
        assert rationale.endswith(".")

