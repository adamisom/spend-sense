#!/usr/bin/env python3
"""
Phase 1 Validation Script
Tests the core functionality implemented so far:
- Project structure
- Database schema 
- Signal schema
- Synthetic data generation (users + accounts)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.features.schema import UserSignals, validate_signal_completeness
from src.db.connection import initialize_db, database_transaction
from src.ingest.data_generator import SyntheticDataGenerator
import tempfile

def test_signal_schema():
    """Test UserSignals schema works correctly."""
    print("🧪 Testing UserSignals schema...")
    
    # Test valid signals
    signals = UserSignals(
        credit_utilization_max=0.65,
        has_interest_charges=True,
        subscription_count=3,
        monthly_subscription_spend=89.99
    )
    
    # Test JSON serialization
    json_str = signals.model_dump_json()
    assert len(json_str) > 100, "JSON serialization too short"
    
    # Test validation
    issues = validate_signal_completeness(signals)
    assert isinstance(issues, list), "Validation should return list"
    
    print("✅ Signal schema validation passed")

def test_database_schema():
    """Test database schema and connection."""
    print("🗄️ Testing database schema...")
    
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name
    
    try:
        # Test initialization
        initialize_db(db_path=test_db)
        
        # Test transaction
        with database_transaction(test_db) as conn:
            conn.execute("INSERT INTO users (user_id) VALUES (?)", ("test_user",))
            
        # Verify data
        with database_transaction(test_db) as conn:
            result = conn.execute("SELECT user_id FROM users").fetchone()
            assert result['user_id'] == 'test_user'
            
        print("✅ Database schema validation passed")
        
    finally:
        # Cleanup
        if os.path.exists(test_db):
            os.remove(test_db)

def test_synthetic_data_generation():
    """Test synthetic data generator."""
    print("🏭 Testing synthetic data generation...")
    
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate small dataset
    data = generator.generate_all(5)
    
    # Validate users
    assert len(data['users']) == 5, f"Expected 5 users, got {len(data['users'])}"
    assert all('user_id' in user for user in data['users']), "Missing user_id fields"
    
    # Validate accounts
    assert len(data['accounts']) >= 5, f"Expected at least 5 accounts, got {len(data['accounts'])}"
    assert all('account_id' in acc for acc in data['accounts']), "Missing account_id fields"
    
    # Check account types
    account_types = set(acc['subtype'] for acc in data['accounts'])
    assert 'checking' in account_types, "No checking accounts generated"
    
    print("✅ Synthetic data generation validation passed")

def main():
    """Run all Phase 1 validation tests."""
    print("🚀 Starting Phase 1 Validation Tests\n")
    
    try:
        test_signal_schema()
        print()
        
        test_database_schema() 
        print()
        
        test_synthetic_data_generation()
        print()
        
        print("🎉 All Phase 1 validation tests passed!")
        print("Ready for Phase 1.4: Data Loading Pipeline")
        
    except Exception as e:
        print(f"❌ Phase 1 validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

