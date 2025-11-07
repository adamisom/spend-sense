"""
Tests for guardrails
"""
import pytest
from unittest.mock import patch, MagicMock
from src.guardrails.guardrails import Guardrails, GuardrailViolation
from src.recommend.content_schema import ContentItem, ContentType
from src.recommend.recommendation_engine import Recommendation

class TestGuardrails:
    """Test guardrails functionality."""
    
    def test_consent_check_passed(self, temp_db_path):
        """Test consent check when user has consented."""
        guardrails = Guardrails()
        
        with patch('src.guardrails.guardrails.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.return_value = True
            mock_conn.execute.return_value.fetchone.return_value = mock_row
            mock_db.return_value.__enter__.return_value = mock_conn
            
            result = guardrails.check_consent("user_with_consent")
            assert result is True
    
    def test_consent_check_failed(self, temp_db_path):
        """Test consent check raises GuardrailViolation when no consent."""
        guardrails = Guardrails()
        
        with patch('src.guardrails.guardrails.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.return_value = False
            mock_conn.execute.return_value.fetchone.return_value = mock_row
            mock_db.return_value.__enter__.return_value = mock_conn
            
            with pytest.raises(GuardrailViolation) as exc_info:
                guardrails.check_consent("user_without_consent")
            assert "not consented" in exc_info.value.reason.lower()
    
    def test_consent_check_missing_user(self, temp_db_path):
        """Test consent check handles missing user gracefully."""
        guardrails = Guardrails()
        
        with patch('src.guardrails.guardrails.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None
            mock_db.return_value.__enter__.return_value = mock_conn
            
            with pytest.raises(GuardrailViolation) as exc_info:
                guardrails.check_consent("nonexistent_user")
            assert "not found" in exc_info.value.reason.lower()
    
    def test_prohibited_pattern_detection(self):
        """Test that prohibited patterns are detected."""
        guardrails = Guardrails()
        content = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="You're stupid with money",
            description="This is a test",
            personas=["high_utilization"],
            url="/test"
        )
        
        with pytest.raises(GuardrailViolation) as exc_info:
            guardrails.validate_content_safety(content)
        assert "prohibited pattern" in exc_info.value.reason.lower()
    
    def test_positive_framing_enforcement(self):
        """Test that negative language is rewritten."""
        guardrails = Guardrails()
        text = "You can't afford this expensive item"
        result = guardrails.enforce_positive_framing(text)
        
        # Should rewrite negative language
        assert "can't afford" not in result.lower() or "can work toward" in result.lower()
    
    def test_disclaimer_injection(self):
        """Test that disclaimers are injected for partner offers."""
        guardrails = Guardrails()
        rec = Recommendation(
            rec_id="test",
            content_id="test",
            title="Test",
            description="Test",
            url="/test",
            type="partner_offer",
            reading_time_minutes=5,
            rationale="This is a great offer",
            priority_score=5.0,
            match_reasons=[]
        )
        
        filtered = guardrails.filter_recommendations([rec])
        assert len(filtered) == 1
        assert "partner offer" in filtered[0].rationale.lower() or "compensation" in filtered[0].rationale.lower()
    
    def test_rate_limit_within_limit(self, temp_db_path):
        """Test rate limit check when under limit."""
        guardrails = Guardrails()
        
        with patch('src.guardrails.guardrails.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.return_value = 5  # Under limit of 10
            mock_conn.execute.return_value.fetchone.return_value = mock_row
            mock_db.return_value.__enter__.return_value = mock_conn
            
            result = guardrails.check_rate_limit("user_under_limit")
            assert result is True
    
    def test_rate_limit_exceeded(self, temp_db_path):
        """Test rate limit check when exceeded."""
        guardrails = Guardrails()
        
        with patch('src.guardrails.guardrails.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.return_value = 15  # Over limit of 10
            mock_conn.execute.return_value.fetchone.return_value = mock_row
            mock_db.return_value.__enter__.return_value = mock_conn
            
            with pytest.raises(GuardrailViolation) as exc_info:
                guardrails.check_rate_limit("user_over_limit")
            assert "exceeded" in exc_info.value.reason.lower()
    
    def test_filter_recommendations_removes_unsafe(self):
        """Test that unsafe recommendations are filtered out."""
        guardrails = Guardrails()
        
        safe_rec = Recommendation(
            rec_id="safe",
            content_id="safe",
            title="Safe Content",
            description="This is safe content",
            url="/safe",
            type="article",
            reading_time_minutes=5,
            rationale="This is safe",
            priority_score=5.0,
            match_reasons=[]
        )
        
        # Create rec with prohibited pattern in rationale
        unsafe_rec = Recommendation(
            rec_id="unsafe",
            content_id="unsafe",
            title="Unsafe",
            description="Test",
            url="/unsafe",
            type="article",
            reading_time_minutes=5,
            rationale="You're stupid with money",  # Prohibited pattern
            priority_score=5.0,
            match_reasons=[]
        )
        
        filtered = guardrails.filter_recommendations([safe_rec, unsafe_rec])
        assert len(filtered) == 1
        assert filtered[0].rec_id == "safe"

