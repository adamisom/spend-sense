# Phase 3 Testing Opportunities - High-Value Unit Tests

## 🎯 Overview

This document identifies high-value unit testing opportunities for Phase 3 components (Evaluation Metrics Engine and Dashboard utilities). These tests focus on **business logic** and **calculation correctness** rather than UI rendering.

---

## 1. 📊 Evaluation Metrics Engine Tests (HIGH PRIORITY)

### Why These Are High-Value
- **Pure calculation functions** - easy to test with mock data
- **Business-critical logic** - metrics drive decision-making
- **Edge cases matter** - empty data, missing fields, division by zero
- **Regression prevention** - calculations can break silently

### Test File: `tests/test_evaluation_metrics.py`

#### 1.1 Coverage Metrics Calculation
**Function**: `_calculate_coverage_metrics()`

**Test Cases**:
```python
def test_coverage_metrics_empty_recommendations():
    """Test coverage metrics when no recommendations exist."""
    # Should return 0% coverage for all metrics

def test_coverage_metrics_full_coverage():
    """Test 100% user coverage scenario."""
    # All users have recommendations

def test_coverage_metrics_partial_coverage():
    """Test partial coverage (e.g., 50% of users)."""
    # Verify percentage calculation is correct

def test_persona_coverage_distribution():
    """Test persona coverage percentages."""
    # Multiple personas, verify distribution sums correctly

def test_content_coverage_with_catalog():
    """Test content coverage calculation."""
    # Mock catalog, verify used vs total calculation

def test_content_coverage_catalog_load_failure():
    """Test graceful handling when catalog can't be loaded."""
    # Should return 0.0, not crash
```

**Value**: Ensures coverage calculations are mathematically correct and handle edge cases.

---

#### 1.2 Quality Metrics Calculation
**Function**: `_calculate_quality_metrics()`

**Test Cases**:
```python
def test_quality_metrics_empty_data():
    """Test quality metrics with empty recommendations."""
    # Should return zeros

def test_avg_recommendations_per_user():
    """Test average recommendations calculation."""
    # Users with varying rec counts, verify mean

def test_recommendation_diversity():
    """Test content type diversity calculation."""
    # Users with different content type mixes
    # Verify average unique types per user

def test_rationale_quality_percentage():
    """Test rationale quality percentage."""
    # Mix of recommendations with/without rationales
    # Verify percentage calculation

def test_diversity_with_missing_content_types():
    """Test diversity when content catalog missing items."""
    # Should handle gracefully, return 0.0
```

**Value**: Validates quality metrics that indicate recommendation system health.

---

#### 1.3 Performance Metrics Calculation
**Function**: `_calculate_performance_metrics()`

**Test Cases**:
```python
def test_error_rate_calculation():
    """Test error rate (users with signals but no recs)."""
    # Users with signals but no recommendations
    # Verify percentage calculation

def test_error_rate_no_signals():
    """Test error rate when no signals exist."""
    # Should return 100% error rate

def test_error_rate_all_successful():
    """Test error rate when all users have recommendations."""
    # Should return 0% error rate

def test_data_quality_correlation():
    """Test data quality impact correlation calculation."""
    # Mock signals with varying data quality scores
    # Mock recommendation counts
    # Verify correlation calculation using numpy.corrcoef

def test_data_quality_correlation_insufficient_data():
    """Test correlation with < 2 data points."""
    # Should return 0.0 (can't calculate correlation)

def test_data_quality_correlation_negative():
    """Test that negative correlations are clamped to 0."""
    # Verify max(0.0, correlation * 100) logic

def test_data_quality_correlation_missing_signals():
    """Test when signals column missing or malformed."""
    # Should handle gracefully, return 0.0
```

**Value**: Performance metrics are critical for system monitoring and alerting.

---

#### 1.4 Business Metrics Calculation
**Function**: `_calculate_business_metrics()`

**Test Cases**:
```python
def test_partner_offer_rate():
    """Test partner offer percentage calculation."""
    # Mix of partner_offer and other content types
    # Verify percentage

def test_educational_content_rate():
    """Test educational content percentage."""
    # Articles, checklists, calculators vs partner offers
    # Verify percentage

def test_business_metrics_empty_data():
    """Test with empty recommendations."""
    # Should return 0.0 for both rates

def test_business_metrics_catalog_missing():
    """Test when content catalog can't be loaded."""
    # Should return 0.0, not crash

def test_business_metrics_unknown_content_types():
    """Test with content_ids not in catalog."""
    # Should handle gracefully
```

**Value**: Business metrics track revenue and educational goals.

---

#### 1.5 Guardrails Compliance Metrics
**Function**: `_calculate_guardrails_metrics()`

**Test Cases**:
```python
def test_consent_compliance_100_percent():
    """Test when all recommendations are to consented users."""
    # All users have consent_status=True
    # Should return 100%

def test_consent_compliance_violations():
    """Test consent compliance with violations."""
    # Some users without consent receiving recommendations
    # Verify percentage calculation

def test_consent_compliance_no_recommendations():
    """Test when no recommendations exist."""
    # Should return 0.0 for consent, 100.0 for eligibility

def test_consent_compliance_empty_users():
    """Test with empty users DataFrame."""
    # Should handle gracefully

def test_eligibility_compliance():
    """Test eligibility compliance (currently always 100%)."""
    # Future: when eligibility checking is implemented
```

**Value**: **CRITICAL** - Consent compliance is a legal requirement. Must be 100%.

---

#### 1.6 Report Generation
**Function**: `generate_evaluation_report()`

**Test Cases**:
```python
def test_report_generation_basic():
    """Test report generation with valid results."""
    # Verify all sections present
    # Verify formatting

def test_report_success_criteria_assessment():
    """Test success criteria checkmarks."""
    # Test ✅ vs ❌ logic for MVP targets
    # User Coverage ≥30%
    # Error Rate ≤20%
    # P95 Compute Time ≤500ms
    # Consent Compliance 100%

def test_report_with_empty_persona_coverage():
    """Test report when no persona data."""
    # Should handle gracefully

def test_report_timestamp_formatting():
    """Test timestamp formatting in report."""
    # Verify ISO format or readable format
```

**Value**: Reports are used for decision-making; formatting errors reduce trust.

---

#### 1.7 Integration Test: Full Evaluation
**Function**: `evaluate_system()`

**Test Cases**:
```python
def test_evaluate_system_with_mock_db():
    """Test full evaluation with mocked database."""
    # Mock all database queries
    # Verify all metric categories calculated
    # Verify EvaluationResults structure

def test_evaluate_system_empty_database():
    """Test evaluation with no data."""
    # Should return _empty_results()

def test_evaluate_system_exception_handling():
    """Test exception handling during evaluation."""
    # Mock database errors
    # Should return _empty_results(), not crash
```

**Value**: End-to-end validation of the evaluation pipeline.

---

## 2. 🎨 Dashboard Utilities Tests (MEDIUM PRIORITY)

### Why These Are Medium-Value
- Dashboard is mostly UI (harder to unit test)
- But some data processing functions can be tested
- Lower business impact than evaluation metrics

### Test File: `tests/test_dashboard_utils.py` (if utilities extracted)

#### 2.1 System Health Queries
**Function**: `get_system_health()` (from `streamlit_app.py`)

**Test Cases**:
```python
def test_system_health_calculation():
    """Test system health metrics calculation."""
    # Mock database queries
    # Verify all metrics calculated correctly

def test_system_health_empty_database():
    """Test health with no data."""
    # Should return error status

def test_system_health_signal_coverage_calculation():
    """Test signal coverage percentage."""
    # Verify division by zero protection
```

**Note**: These tests would require extracting the query logic from Streamlit app into a testable module (see Refactoring Opportunities #6).

---

## 3. 📋 Test Data Fixtures

### Add to `tests/conftest.py`:

```python
@pytest.fixture
def sample_users_df():
    """Create sample users DataFrame for testing."""
    return pd.DataFrame({
        'user_id': ['user1', 'user2', 'user3'],
        'consent_status': [True, True, False]
    })

@pytest.fixture
def sample_recommendations_df():
    """Create sample recommendations DataFrame."""
    return pd.DataFrame({
        'rec_id': ['rec1', 'rec2', 'rec3'],
        'user_id': ['user1', 'user1', 'user2'],
        'content_id': ['content1', 'content2', 'content1'],
        'rationale': ['Rationale 1', 'Rationale 2', None],
        'created_at': [
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ],
        'persona': ['high_utilization', 'high_utilization', 'variable_income']
    })

@pytest.fixture
def sample_signals_df():
    """Create sample signals DataFrame."""
    import json
    return pd.DataFrame({
        'user_id': ['user1', 'user2'],
        'signals': [
            json.dumps({'data_quality_score': 0.9}),
            json.dumps({'data_quality_score': 0.7})
        ],
        'window': ['180d', '180d']
    })

@pytest.fixture
def mock_content_catalog(monkeypatch):
    """Mock content catalog for testing."""
    from unittest.mock import MagicMock
    catalog = MagicMock()
    catalog.items = [
        MagicMock(content_id='content1', type=MagicMock(value='article')),
        MagicMock(content_id='content2', type=MagicMock(value='partner_offer')),
    ]
    monkeypatch.setattr('src.evaluation.metrics.load_content_catalog', 
                        lambda x: catalog)
    return catalog
```

---

## 4. 🎯 Testing Strategy

### Priority Order:
1. **Guardrails Compliance Tests** (CRITICAL - legal requirement)
2. **Coverage Metrics Tests** (HIGH - core business metric)
3. **Performance Metrics Tests** (HIGH - system health)
4. **Quality Metrics Tests** (MEDIUM - user experience)
5. **Business Metrics Tests** (MEDIUM - revenue tracking)
6. **Report Generation Tests** (LOW - formatting)

### Test Coverage Goals:
- **Evaluation Metrics Engine**: 80%+ coverage
- **Calculation functions**: 100% coverage (they're pure functions)
- **Edge cases**: All division-by-zero, empty data, missing fields

### Mock Strategy:
- **Database queries**: Mock `database_transaction` context manager
- **Content catalog**: Mock `load_content_catalog` function
- **DataFrames**: Use pandas fixtures with known data

---

## 5. 📊 Expected Test Count

### Evaluation Metrics Tests:
- Coverage metrics: ~6 tests
- Quality metrics: ~5 tests
- Performance metrics: ~7 tests
- Business metrics: ~5 tests
- Guardrails metrics: ~5 tests
- Report generation: ~4 tests
- Integration: ~3 tests

**Total**: ~35 new tests for evaluation metrics

### Dashboard Tests:
- System health: ~3 tests (if utilities extracted)

**Total**: ~38 new tests for Phase 3

---

## 6. ✅ Success Criteria

Tests are successful when:
- ✅ All calculation functions have 100% branch coverage
- ✅ All edge cases (empty data, missing fields) are handled
- ✅ Guardrails compliance tests verify 100% requirement
- ✅ Performance metrics tests verify correlation calculations
- ✅ Report generation tests verify formatting correctness
- ✅ All tests run in < 5 seconds (fast feedback)

---

## 7. 🚀 Implementation Notes

1. **Start with guardrails tests** - most critical
2. **Use fixtures from conftest.py** - reuse test data
3. **Mock external dependencies** - database, file I/O
4. **Test edge cases first** - catch bugs early
5. **Keep tests fast** - use mocks, not real database

---

## 8. 📝 Example Test Structure

```python
import pytest
import pandas as pd
from datetime import datetime
from src.evaluation.metrics import RecommendationEvaluator, EvaluationResults

class TestCoverageMetrics:
    """Test coverage metrics calculations."""
    
    def test_empty_recommendations(self, sample_users_df):
        """Test coverage with no recommendations."""
        evaluator = RecommendationEvaluator()
        result = evaluator._calculate_coverage_metrics(
            sample_users_df, 
            pd.DataFrame()
        )
        assert result['user_coverage'] == 0.0
        assert result['content_coverage'] == 0.0
        assert result['persona_coverage'] == {}
    
    def test_full_coverage(self, sample_users_df, sample_recommendations_df):
        """Test 100% user coverage."""
        evaluator = RecommendationEvaluator()
        result = evaluator._calculate_coverage_metrics(
            sample_users_df,
            sample_recommendations_df
        )
        # All 3 users should have recommendations
        assert result['user_coverage'] == pytest.approx(100.0, abs=0.1)
```

---

## Summary

**High-Value Tests**: 35+ tests for evaluation metrics engine
**Focus Areas**: 
- Guardrails compliance (legal requirement)
- Coverage calculations (business metrics)
- Performance metrics (system health)
- Edge case handling (robustness)

**Estimated Effort**: 4-6 hours for comprehensive test suite
**ROI**: High - prevents calculation bugs, ensures compliance, enables confident refactoring

