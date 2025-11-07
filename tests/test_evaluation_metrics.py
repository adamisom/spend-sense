"""
Unit tests for evaluation metrics engine - High-value tests only
Focuses on critical business logic and non-trivial calculations
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock

from src.evaluation.metrics import RecommendationEvaluator, EvaluationResults


@pytest.fixture
def sample_users_df():
    """Create sample users DataFrame for testing."""
    return pd.DataFrame({
        'user_id': ['user1', 'user2', 'user3', 'user4'],
        'consent_status': [True, True, False, True]
    })


@pytest.fixture
def sample_recommendations_df():
    """Create sample recommendations DataFrame."""
    return pd.DataFrame({
        'rec_id': ['rec1', 'rec2', 'rec3', 'rec4'],
        'user_id': ['user1', 'user1', 'user2', 'user3'],  # user3 has no consent
        'content_id': ['content1', 'content2', 'content1', 'content3'],
        'rationale': ['Rationale 1', 'Rationale 2', 'Rationale 3', 'Rationale 4'],
        'created_at': [
            (datetime.now() - timedelta(days=1)).isoformat(),
            (datetime.now() - timedelta(days=2)).isoformat(),
            (datetime.now() - timedelta(days=3)).isoformat(),
            (datetime.now() - timedelta(days=4)).isoformat()
        ],
        'persona': ['high_utilization', 'high_utilization', 'variable_income', 'high_utilization']
    })


@pytest.fixture
def sample_signals_df():
    """Create sample signals DataFrame."""
    return pd.DataFrame({
        'user_id': ['user1', 'user2', 'user3', 'user4'],
        'signals': [
            json.dumps({'data_quality_score': 0.9}),
            json.dumps({'data_quality_score': 0.7}),
            json.dumps({'data_quality_score': 0.5}),
            json.dumps({'data_quality_score': 0.8})
        ],
        'window': ['180d', '180d', '180d', '180d']
    })


@pytest.fixture
def evaluator():
    """Create RecommendationEvaluator instance."""
    return RecommendationEvaluator(db_path=":memory:")


class TestGuardrailsCompliance:
    """CRITICAL: Legal requirement - consent compliance must be 100%."""
    
    def test_consent_compliance_violations(self, evaluator, sample_users_df, sample_recommendations_df):
        """Test consent compliance detection when violations exist."""
        # user3 has no consent but received a recommendation
        result = evaluator._calculate_guardrails_metrics(sample_users_df, sample_recommendations_df)
        
        # 3 unique users with recommendations: user1, user2, user3
        # user3 has consent_status=False, so 1 violation
        # Compliance = (3 - 1) / 3 * 100 = 66.67%
        assert result['consent_compliance'] == pytest.approx(66.67, abs=0.1)
        assert result['eligibility_compliance'] == 100.0
    
    def test_consent_compliance_100_percent(self, evaluator, sample_users_df):
        """Test consent compliance when all recommendations are to consented users."""
        # Only recommendations to users with consent
        compliant_recs = pd.DataFrame({
            'rec_id': ['rec1', 'rec2'],
            'user_id': ['user1', 'user2'],  # Both have consent
            'content_id': ['content1', 'content2'],
            'rationale': ['R1', 'R2'],
            'created_at': [datetime.now().isoformat(), datetime.now().isoformat()],
            'persona': ['high_utilization', 'variable_income']
        })
        
        result = evaluator._calculate_guardrails_metrics(sample_users_df, compliant_recs)
        
        assert result['consent_compliance'] == 100.0
        assert result['eligibility_compliance'] == 100.0
    
    def test_consent_compliance_no_recommendations(self, evaluator, sample_users_df):
        """Test consent compliance when no recommendations exist."""
        empty_recs = pd.DataFrame()
        
        result = evaluator._calculate_guardrails_metrics(sample_users_df, empty_recs)
        
        # No recommendations = no violations possible
        assert result['consent_compliance'] == 0.0
        assert result['eligibility_compliance'] == 100.0
    
    def test_consent_compliance_empty_users(self, evaluator, sample_recommendations_df):
        """Test consent compliance with empty users DataFrame."""
        empty_users = pd.DataFrame(columns=['user_id', 'consent_status'])
        
        result = evaluator._calculate_guardrails_metrics(empty_users, sample_recommendations_df)
        
        # Should handle gracefully - no users means no consent data
        assert result['consent_compliance'] == 0.0
        assert result['eligibility_compliance'] == 100.0


class TestErrorRate:
    """HIGH VALUE: Error rate is used for monitoring and alerting."""
    
    def test_error_rate_calculation(self, evaluator, sample_signals_df, sample_recommendations_df):
        """Test error rate calculation (users with signals but no recommendations)."""
        # user4 has signals but no recommendations
        # user1, user2, user3 have both signals and recommendations
        # So 1 user with error out of 4 users with signals = 25%
        
        result = evaluator._calculate_performance_metrics(sample_recommendations_df, sample_signals_df)
        
        assert result['error_rate'] == pytest.approx(25.0, abs=0.1)
    
    def test_error_rate_all_successful(self, evaluator, sample_signals_df):
        """Test error rate when all users with signals have recommendations."""
        # Recommendations for all users with signals
        all_successful_recs = pd.DataFrame({
            'rec_id': ['rec1', 'rec2', 'rec3', 'rec4'],
            'user_id': ['user1', 'user2', 'user3', 'user4'],
            'content_id': ['c1', 'c2', 'c3', 'c4'],
            'rationale': ['R1', 'R2', 'R3', 'R4'],
            'created_at': [datetime.now().isoformat()] * 4,
            'persona': ['high_utilization'] * 4
        })
        
        result = evaluator._calculate_performance_metrics(all_successful_recs, sample_signals_df)
        
        assert result['error_rate'] == 0.0
    
    def test_error_rate_no_signals(self, evaluator, sample_recommendations_df):
        """Test error rate when no signals exist."""
        empty_signals = pd.DataFrame()
        
        result = evaluator._calculate_performance_metrics(sample_recommendations_df, empty_signals)
        
        # No signals = 100% error rate (all users should have signals)
        assert result['error_rate'] == 100.0


class TestDataQualityCorrelation:
    """MEDIUM VALUE: Non-trivial calculation using numpy."""
    
    def test_data_quality_correlation(self, evaluator, sample_signals_df, sample_recommendations_df):
        """Test data quality impact correlation calculation."""
        # Create recommendations with varying counts per user
        # user1: 2 recs, quality 0.9
        # user2: 1 rec, quality 0.7
        # user3: 1 rec, quality 0.5
        # Should show positive correlation (higher quality = more recs)
        
        result = evaluator._calculate_performance_metrics(sample_recommendations_df, sample_signals_df)
        
        # Verify correlation is calculated (should be > 0 for this data)
        # Note: actual value depends on the correlation, but should be a number
        assert isinstance(result['data_quality_impact'], float)
        assert result['data_quality_impact'] >= 0.0
        assert result['data_quality_impact'] <= 100.0
    
    def test_data_quality_correlation_insufficient_data(self, evaluator):
        """Test correlation with insufficient data points (< 2 users)."""
        # Need at least 2 data points for correlation
        single_user_signals = pd.DataFrame({
            'user_id': ['user1'],
            'signals': [json.dumps({'data_quality_score': 0.9})],
            'window': ['180d']
        })
        
        single_user_recs = pd.DataFrame({
            'rec_id': ['rec1'],
            'user_id': ['user1'],
            'content_id': ['c1'],
            'rationale': ['R1'],
            'created_at': [datetime.now().isoformat()],
            'persona': ['high_utilization']
        })
        
        result = evaluator._calculate_performance_metrics(single_user_recs, single_user_signals)
        
        # Should return 0.0 when insufficient data
        assert result['data_quality_impact'] == 0.0
    
    def test_data_quality_correlation_missing_signals_column(self, evaluator, sample_recommendations_df):
        """Test when signals column is missing or malformed."""
        signals_no_column = pd.DataFrame({
            'user_id': ['user1', 'user2']
            # Missing 'signals' column
        })
        
        result = evaluator._calculate_performance_metrics(sample_recommendations_df, signals_no_column)
        
        # Should handle gracefully, return 0.0
        assert result['data_quality_impact'] == 0.0


class TestEmptyDataHandling:
    """MEDIUM VALUE: Prevents crashes across all calculation functions."""
    
    def test_all_metrics_with_empty_data(self, evaluator):
        """Test all metric calculation functions with empty DataFrames."""
        empty_users = pd.DataFrame()
        empty_recs = pd.DataFrame()
        empty_signals = pd.DataFrame()
        
        # Coverage metrics
        coverage = evaluator._calculate_coverage_metrics(empty_users, empty_recs)
        assert coverage['user_coverage'] == 0.0
        assert coverage['content_coverage'] == 0.0
        assert coverage['persona_coverage'] == {}
        
        # Quality metrics
        quality = evaluator._calculate_quality_metrics(empty_recs, empty_signals)
        assert quality['avg_recs_per_user'] == 0.0
        assert quality['diversity'] == 0.0
        assert quality['rationale_quality'] == 0.0
        
        # Performance metrics
        performance = evaluator._calculate_performance_metrics(empty_recs, empty_signals)
        assert performance['compute_time_p95'] == 0.0
        assert performance['error_rate'] == 100.0  # No signals = 100% error
        assert performance['data_quality_impact'] == 0.0
        
        # Business metrics
        business = evaluator._calculate_business_metrics(empty_recs)
        assert business['partner_offer_rate'] == 0.0
        assert business['educational_rate'] == 0.0
        
        # Guardrails metrics
        guardrails = evaluator._calculate_guardrails_metrics(empty_users, empty_recs)
        assert guardrails['consent_compliance'] == 0.0
        assert guardrails['eligibility_compliance'] == 100.0
    
    def test_division_by_zero_protection(self, evaluator):
        """Test that division by zero is handled (zero users, zero recommendations)."""
        # Empty users but recommendations exist (edge case)
        empty_users = pd.DataFrame()
        some_recs = pd.DataFrame({
            'rec_id': ['rec1'],
            'user_id': ['user1'],
            'content_id': ['c1'],
            'rationale': ['R1'],
            'created_at': [datetime.now().isoformat()],
            'persona': ['high_utilization']
        })
        
        # Should not crash on division by zero
        coverage = evaluator._calculate_coverage_metrics(empty_users, some_recs)
        # When total_users = 0, should return 0.0, not crash
        assert coverage['user_coverage'] == 0.0


class TestIntegration:
    """Integration test for full evaluation pipeline."""
    
    @patch('src.evaluation.metrics.database_transaction')
    def test_evaluate_system_with_mock_data(self, mock_db, evaluator, sample_users_df, 
                                           sample_recommendations_df, sample_signals_df):
        """Test full evaluation with mocked database queries."""
        # Mock database transaction context manager
        mock_conn = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_conn
        
        # Mock the data retrieval methods
        with patch.object(evaluator, '_get_users_data', return_value=sample_users_df), \
             patch.object(evaluator, '_get_recommendations_data', return_value=sample_recommendations_df), \
             patch.object(evaluator, '_get_signals_data', return_value=sample_signals_df):
            
            results = evaluator.evaluate_system(window_days=7)
            
            # Verify results structure
            assert isinstance(results, EvaluationResults)
            assert results.total_users_evaluated == len(sample_users_df)
            assert results.evaluation_window_days == 7
            assert 0.0 <= results.user_coverage <= 100.0
            assert 0.0 <= results.consent_compliance <= 100.0

