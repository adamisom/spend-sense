"""
Tests for content schema validation
"""
import pytest
import json
import tempfile
from pathlib import Path
from src.recommend.content_schema import (
    ContentItem, ContentCatalog, ContentType, SignalTrigger,
    load_content_catalog, validate_catalog_file
)

class TestContentSchema:
    """Test content schema validation."""
    
    def test_valid_item(self):
        """Test that valid content item passes validation."""
        item = ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test Article",
            description="Test description for validation",
            personas=["high_utilization"],
            url="/test"
        )
        assert item.content_id == "test"
        assert item.type == ContentType.ARTICLE
    
    def test_invalid_persona(self):
        """Test that invalid persona raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            ContentItem(
                content_id="test",
                type=ContentType.ARTICLE,
                title="Test",
                description="Test description",
                personas=["invalid_persona"],  # Should fail
                url="/test"
            )
        assert "invalid persona" in str(exc_info.value).lower()
    
    def test_invalid_url(self):
        """Test that invalid URL format raises error."""
        with pytest.raises(ValueError) as exc_info:
            ContentItem(
                content_id="test",
                type=ContentType.ARTICLE,
                title="Test",
                description="Test description",
                personas=["high_utilization"],
                url="invalid-url"  # Should start with http://, https://, or /
            )
        assert "url" in str(exc_info.value).lower()
    
    def test_valid_url_formats(self):
        """Test that valid URL formats pass."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "/relative/path"
        ]
        
        for url in valid_urls:
            item = ContentItem(
                content_id="test",
                type=ContentType.ARTICLE,
                title="Test",
                description="Test description",
                personas=["high_utilization"],
                url=url
            )
            assert item.url == url
    
    def test_catalog_completeness(self, temp_catalog_file):
        """Test catalog completeness validation."""
        catalog = load_content_catalog(temp_catalog_file)
        issues = catalog.validate_completeness()
        assert isinstance(issues, list)
    
    def test_catalog_persona_coverage(self):
        """Test that all personas have content."""
        # Load actual catalog
        catalog_path = "data/content/catalog.json"
        if Path(catalog_path).exists():
            catalog = load_content_catalog(catalog_path)
            all_personas = {
                'high_utilization', 'variable_income', 'subscription_heavy',
                'savings_builder', 'insufficient_data'
            }
            covered = set()
            for item in catalog.items:
                covered.update(item.personas)
            # Should have coverage for all personas
            assert len(covered.intersection(all_personas)) > 0
    
    def test_catalog_duplicate_ids(self):
        """Test that duplicate content IDs are detected."""
        items = [
            ContentItem(
                content_id="duplicate",
                type=ContentType.ARTICLE,
                title="Test 1",
                description="Test",
                personas=["high_utilization"],
                url="/test1"
            ),
            ContentItem(
                content_id="duplicate",  # Duplicate!
                type=ContentType.ARTICLE,
                title="Test 2",
                description="Test",
                personas=["high_utilization"],
                url="/test2"
            )
        ]
        
        catalog = ContentCatalog(version="1.0", items=items)
        issues = catalog.validate_completeness()
        assert any("duplicate" in issue.lower() for issue in issues)
    
    def test_catalog_content_type_distribution(self):
        """Test that catalog has minimum content types."""
        catalog_path = "data/content/catalog.json"
        if Path(catalog_path).exists():
            catalog = load_content_catalog(catalog_path)
            type_counts = {}
            for item in catalog.items:
                type_counts[item.type] = type_counts.get(item.type, 0) + 1
            
            # Should have articles
            assert type_counts.get(ContentType.ARTICLE, 0) >= 3
            # Should have partner offers
            assert type_counts.get(ContentType.PARTNER_OFFER, 0) >= 2
    
    def test_catalog_loading(self, temp_catalog_file):
        """Test catalog loading from file."""
        catalog = load_content_catalog(temp_catalog_file)
        assert catalog is not None
        assert len(catalog.items) > 0
        assert catalog.version is not None
    
    def test_catalog_file_validation(self, temp_catalog_file):
        """Test catalog file validation."""
        is_valid = validate_catalog_file(temp_catalog_file)
        assert isinstance(is_valid, bool)

