"""
Pytest configuration and shared fixtures
"""
import pytest
import tempfile
import os
from pathlib import Path

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from src.features.schema import UserSignals
from src.recommend.content_schema import ContentItem, ContentType, ContentCatalog, SignalTrigger

@pytest.fixture
def sample_signals():
    """Create sample UserSignals for testing."""
    return UserSignals(
        credit_utilization_max=0.75,
        has_interest_charges=True,
        is_overdue=False,
        minimum_payment_only=False,
        income_pay_gap=30,
        cash_flow_buffer=2.0,
        income_variability=0.2,
        subscription_count=3,
        monthly_subscription_spend=50.0,
        subscription_share=0.1,
        savings_growth_rate=0.05,
        monthly_savings_inflow=200.0,
        emergency_fund_months=3.0,
        insufficient_data=False,
        data_quality_score=0.9
    )

@pytest.fixture
def sample_content_item():
    """Create sample ContentItem for testing."""
    return ContentItem(
        content_id="test_article",
        type=ContentType.ARTICLE,
        title="Test Article",
        description="Test description for unit testing",
        personas=["high_utilization"],
        signal_triggers=[SignalTrigger.HIGH_CREDIT_UTILIZATION],
        url="/test/article",
        reading_time_minutes=10,
        priority_score=8.0
    )

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary directory for test configs."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def temp_catalog_file(tmp_path):
    """Create temporary catalog file for testing."""
    catalog_file = tmp_path / "catalog.json"
    catalog_data = {
        "version": "1.0",
        "last_updated": "2025-01-01T00:00:00Z",
        "items": [
            {
                "content_id": "test_article",
                "type": "article",
                "title": "Test Article",
                "description": "Test description",
                "personas": ["high_utilization"],
                "signal_triggers": ["high_credit_utilization"],
                "url": "/test/article",
                "reading_time_minutes": 10,
                "priority_score": 8.0
            }
        ]
    }
    import json
    with open(catalog_file, 'w') as f:
        json.dump(catalog_data, f)
    return str(catalog_file)

@pytest.fixture
def temp_db_path(tmp_path):
    """Create temporary database path for testing."""
    return str(tmp_path / "test.db")

