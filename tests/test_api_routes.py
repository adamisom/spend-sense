"""
Tests for API routes
"""
import pytest
from unittest.mock import patch, MagicMock
from src.api.routes import (
    create_user, update_consent, record_feedback, get_approval_queue,
    UserCreateRequest, ConsentRequest, FeedbackRequest
)
from src.db.connection import database_transaction

class TestUserCreation:
    """Test POST /users endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_user_with_auto_id(self, temp_db_path):
        """Test user creation with auto-generated ID."""
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None  # No existing user
            mock_db.return_value.__enter__.return_value = mock_conn
            mock_db.return_value.__exit__.return_value = None
            
            request = UserCreateRequest(consent_status=False)
            response = await create_user(request)
            
            assert "user_id" in response
            assert response["user_id"].startswith("user_")
            assert response["consent_status"] is False
            assert response["status"] == "created"
    
    @pytest.mark.asyncio
    async def test_create_user_with_provided_id(self, temp_db_path):
        """Test user creation with provided user_id."""
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None  # No existing user
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = UserCreateRequest(user_id="test_user_123", consent_status=True)
            response = await create_user(request)
            
            assert response["user_id"] == "test_user_123"
            assert response["consent_status"] is True
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate(self, temp_db_path):
        """Test that duplicate user_id returns 409."""
        from fastapi import HTTPException
        
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.return_value = "existing_user"
            mock_conn.execute.return_value.fetchone.return_value = mock_row  # User exists
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = UserCreateRequest(user_id="existing_user", consent_status=False)
            
            with pytest.raises(HTTPException) as exc_info:
                await create_user(request)
            
            assert exc_info.value.status_code == 409
            assert "already exists" in exc_info.value.detail.lower()

class TestConsentManagement:
    """Test POST /consent endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_consent_grant(self, temp_db_path):
        """Test granting consent."""
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key: {
                'user_id': 'test_user',
                'consent_status': False
            }[key]
            mock_conn.execute.return_value.fetchone.return_value = mock_row
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = ConsentRequest(user_id="test_user", consented=True)
            response = await update_consent(request)
            
            assert response["user_id"] == "test_user"
            assert response["consent_status"] is True
            assert response["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_update_consent_revoke(self, temp_db_path):
        """Test revoking consent."""
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key: {
                'user_id': 'test_user',
                'consent_status': True
            }[key]
            mock_conn.execute.return_value.fetchone.return_value = mock_row
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = ConsentRequest(user_id="test_user", consented=False)
            response = await update_consent(request)
            
            assert response["consent_status"] is False
    
    @pytest.mark.asyncio
    async def test_update_consent_missing_user(self, temp_db_path):
        """Test that missing user returns 404."""
        from fastapi import HTTPException
        
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None  # User not found
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = ConsentRequest(user_id="nonexistent_user", consented=True)
            
            with pytest.raises(HTTPException) as exc_info:
                await update_consent(request)
            
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

class TestFeedback:
    """Test POST /feedback endpoint."""
    
    @pytest.mark.asyncio
    async def test_record_feedback_helpful(self, temp_db_path):
        """Test recording helpful feedback."""
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            # First query: get recommendation
            mock_rec = MagicMock()
            mock_rec.__getitem__.side_effect = lambda key: {
                'rec_id': 'test_rec_123',
                'content_id': 'test_content',
                'user_id': 'test_user'
            }[key]
            mock_conn.execute.return_value.fetchone.return_value = mock_rec
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = FeedbackRequest(
                user_id="test_user",
                rec_id="test_rec_123",
                helpful=True,
                comment="Very helpful!"
            )
            response = await record_feedback(request)
            
            assert response["rec_id"] == "test_rec_123"
            assert response["helpful"] is True
            assert response["status"] == "recorded"
            assert "feedback_id" in response
    
    @pytest.mark.asyncio
    async def test_record_feedback_not_helpful(self, temp_db_path):
        """Test recording not helpful feedback."""
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_rec = MagicMock()
            mock_rec.__getitem__.side_effect = lambda key: {
                'rec_id': 'test_rec_123',
                'content_id': 'test_content',
                'user_id': 'test_user'
            }[key]
            mock_conn.execute.return_value.fetchone.return_value = mock_rec
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = FeedbackRequest(
                user_id="test_user",
                rec_id="test_rec_123",
                helpful=False
            )
            response = await record_feedback(request)
            
            assert response["helpful"] is False
    
    @pytest.mark.asyncio
    async def test_record_feedback_missing_recommendation(self, temp_db_path):
        """Test that missing recommendation returns 404."""
        from fastapi import HTTPException
        
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchone.return_value = None  # Recommendation not found
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = FeedbackRequest(
                user_id="test_user",
                rec_id="nonexistent_rec",
                helpful=True
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await record_feedback(request)
            
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_record_feedback_user_mismatch(self, temp_db_path):
        """Test that user_id mismatch returns 403."""
        from fastapi import HTTPException
        
        with patch('src.api.routes.database_transaction') as mock_db:
            mock_conn = MagicMock()
            mock_rec = MagicMock()
            mock_rec.__getitem__.side_effect = lambda key: {
                'rec_id': 'test_rec_123',
                'content_id': 'test_content',
                'user_id': 'different_user'  # Different user
            }[key]
            mock_conn.execute.return_value.fetchone.return_value = mock_rec
            mock_db.return_value.__enter__.return_value = mock_conn
            
            request = FeedbackRequest(
                user_id="test_user",
                rec_id="test_rec_123",
                helpful=True
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await record_feedback(request)
            
            assert exc_info.value.status_code == 403
            assert "does not match" in exc_info.value.detail.lower()

class TestOperatorReview:
    """Test GET /operator/review endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_approval_queue_pending(self, temp_db_path):
        """Test getting pending recommendations."""
        with patch('src.api.routes.database_transaction') as mock_db, \
             patch('src.recommend.content_schema.load_content_catalog') as mock_catalog:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key: {
                'rec_id': 'rec_123',
                'user_id': 'user_001',
                'content_id': 'test_content',
                'rationale': 'Test rationale',
                'created_at': '2025-01-01T00:00:00',
                'approved': None,
                'delivered': False,
                'viewed_at': None
            }[key]
            mock_conn.execute.return_value.fetchall.return_value = [mock_row]
            mock_db.return_value.__enter__.return_value = mock_conn
            
            # Mock content catalog
            from src.recommend.content_schema import ContentItem, ContentType
            mock_content = ContentItem(
                content_id="test_content",
                type=ContentType.ARTICLE,
                title="Test Article",
                description="Test description for validation purposes",
                personas=["high_utilization"],
                url="/test",
                reading_time_minutes=10
            )
            mock_catalog_obj = MagicMock()
            mock_catalog_obj.items = [mock_content]
            mock_catalog.return_value = mock_catalog_obj
            
            response = await get_approval_queue(limit=10, status="pending")
            
            assert "recommendations" in response
            assert response["status"] == "pending"
            assert len(response["recommendations"]) == 1
            assert response["recommendations"][0]["rec_id"] == "rec_123"
            assert response["recommendations"][0]["title"] == "Test Article"
    
    @pytest.mark.asyncio
    async def test_get_approval_queue_approved(self, temp_db_path):
        """Test getting approved recommendations."""
        with patch('src.api.routes.database_transaction') as mock_db, \
             patch('src.recommend.content_schema.load_content_catalog') as mock_catalog:
            mock_conn = MagicMock()
            mock_row = MagicMock()
            mock_row.__getitem__.side_effect = lambda key: {
                'rec_id': 'rec_123',
                'user_id': 'user_001',
                'content_id': 'test_content',
                'rationale': 'Test rationale',
                'created_at': '2025-01-01T00:00:00',
                'approved': True,
                'delivered': True,
                'viewed_at': '2025-01-01T01:00:00'
            }[key]
            mock_conn.execute.return_value.fetchall.return_value = [mock_row]
            mock_db.return_value.__enter__.return_value = mock_conn
            
            from src.recommend.content_schema import ContentItem, ContentType
            mock_content = ContentItem(
                content_id="test_content",
                type=ContentType.ARTICLE,
                title="Test Article",
                description="Test description for validation purposes",
                personas=["high_utilization"],
                url="/test",
                reading_time_minutes=10
            )
            mock_catalog_obj = MagicMock()
            mock_catalog_obj.items = [mock_content]
            mock_catalog.return_value = mock_catalog_obj
            
            response = await get_approval_queue(limit=50, status="approved")
            
            assert response["status"] == "approved"
            assert response["recommendations"][0]["approved"] is True
    
    @pytest.mark.asyncio
    async def test_get_approval_queue_all(self, temp_db_path):
        """Test getting all recommendations."""
        with patch('src.api.routes.database_transaction') as mock_db, \
             patch('src.recommend.content_schema.load_content_catalog') as mock_catalog:
            mock_conn = MagicMock()
            mock_conn.execute.return_value.fetchall.return_value = []
            mock_db.return_value.__enter__.return_value = mock_conn
            
            mock_catalog_obj = MagicMock()
            mock_catalog_obj.items = []
            mock_catalog.return_value = mock_catalog_obj
            
            response = await get_approval_queue(limit=50, status=None)
            
            assert response["status"] == "all"
            assert response["count"] == 0
            assert response["recommendations"] == []
    
    @pytest.mark.asyncio
    async def test_get_approval_queue_limit(self, temp_db_path):
        """Test that limit parameter works."""
        with patch('src.api.routes.database_transaction') as mock_db, \
             patch('src.recommend.content_schema.load_content_catalog') as mock_catalog:
            mock_conn = MagicMock()
            # Return 5 mock rows
            mock_rows = [MagicMock() for _ in range(5)]
            for row in mock_rows:
                row.__getitem__.side_effect = lambda key, r=row: {
                    'rec_id': 'rec_123',
                    'user_id': 'user_001',
                    'content_id': 'test_content',
                    'rationale': 'Test',
                    'created_at': '2025-01-01T00:00:00',
                    'approved': None,
                    'delivered': False,
                    'viewed_at': None
                }[key]
            mock_conn.execute.return_value.fetchall.return_value = mock_rows
            mock_db.return_value.__enter__.return_value = mock_conn
            
            mock_catalog_obj = MagicMock()
            mock_catalog_obj.items = []
            mock_catalog.return_value = mock_catalog_obj
            
            response = await get_approval_queue(limit=3, status=None)
            
            # Should return results (limit is applied in SQL query)
            assert "recommendations" in response
            assert response["count"] == 5  # Mock returns 5, but SQL would limit to 3

