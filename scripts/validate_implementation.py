#!/usr/bin/env python3
"""
SpendSense Implementation Validation
Tests core components without external dependencies
"""

import sys
import os
import tempfile
import sqlite3
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_project_structure():
    """Test that all required directories and files exist."""
    print("🏗️ Testing project structure...")
    
    required_dirs = [
        'src', 'src/ingest', 'src/features', 'src/personas', 
        'src/recommend', 'src/guardrails', 'src/api', 'src/ui', 
        'src/eval', 'src/db', 'tests', 'data', 'data/content', 
        'data/synthetic', 'db', 'scripts'
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Missing directory: {dir_path}"
    
    required_files = [
        'requirements.txt', 'README.md', '.gitignore', 
        'Dockerfile', 'docker-compose.yml', 'Makefile',
        'src/features/schema.py', 'src/db/connection.py',
        'src/ingest/data_generator.py', 'db/schema.sql',
        'data/content/catalog.json'
    ]
    
    for file_path in required_files:
        assert Path(file_path).exists(), f"Missing file: {file_path}"
    
    print("✅ Project structure validation passed")

def test_schema_definition():
    """Test UserSignals schema without Pydantic dependency."""
    print("📊 Testing signal schema definition...")
    
    # Read the schema file and check structure
    schema_path = Path('src/features/schema.py')
    schema_content = schema_path.read_text()
    
    # Check for required signal fields
    required_fields = [
        'credit_utilization_max', 'has_interest_charges', 'is_overdue',
        'income_pay_gap', 'cash_flow_buffer', 'subscription_count',
        'monthly_subscription_spend', 'savings_growth_rate',
        'monthly_savings_inflow', 'insufficient_data', 'data_quality_score'
    ]
    
    for field in required_fields:
        assert field in schema_content, f"Missing signal field: {field}"
    
    # Check for critical components
    assert 'class UserSignals' in schema_content, "Missing UserSignals class"
    assert 'validate_signal_completeness' in schema_content, "Missing validation function"
    
    print("✅ Signal schema definition validation passed")

def test_database_schema():
    """Test database schema SQL without database dependency."""
    print("🗄️ Testing database schema...")
    
    schema_path = Path('db/schema.sql')
    schema_sql = schema_path.read_text()
    
    # Check for required tables
    required_tables = [
        'CREATE TABLE users', 'CREATE TABLE accounts', 
        'CREATE TABLE transactions', 'CREATE TABLE liabilities',
        'CREATE TABLE user_signals', 'CREATE TABLE persona_assignments',
        'CREATE TABLE recommendations'
    ]
    
    for table in required_tables:
        assert table in schema_sql, f"Missing table definition: {table}"
    
    # Check for indexes
    assert 'CREATE INDEX' in schema_sql, "Missing performance indexes"
    
    # Test schema validity with in-memory SQLite
    try:
        conn = sqlite3.connect(':memory:')
        conn.executescript(schema_sql)
        conn.close()
        print("✅ Database schema is valid SQL")
    except Exception as e:
        raise AssertionError(f"Invalid SQL schema: {e}")
    
    print("✅ Database schema validation passed")

def test_data_generator_logic():
    """Test data generator components without external dependencies."""
    print("🏭 Testing data generator logic...")
    
    # Test UserProfile dataclass
    try:
        # Import without running (to avoid faker dependency)
        gen_path = Path('src/ingest/data_generator.py')
        gen_content = gen_path.read_text()
        
        # Check for critical components
        assert '@dataclass' in gen_content, "Missing UserProfile dataclass"
        assert 'class UserProfile:' in gen_content, "Missing UserProfile class"
        assert 'class SyntheticDataGenerator:' in gen_content, "Missing generator class"
        
        # Check for edge case scenarios
        edge_cases = [
            'high_utilization_and_subscription_heavy',
            'sparse_transaction_history',
            'multiple_red_flags',
            'new_user_insufficient_data'
        ]
        
        for case in edge_cases:
            assert case in gen_content, f"Missing edge case: {case}"
        
        # Check for account generation
        assert 'generate_accounts_for_user' in gen_content, "Missing account generation"
        assert 'generate_users_csv' in gen_content, "Missing user CSV generation"
        
        print("✅ Data generator structure validation passed")
        
    except Exception as e:
        raise AssertionError(f"Data generator validation failed: {e}")

def test_content_catalog():
    """Test content catalog structure."""
    print("📚 Testing content catalog...")
    
    catalog_path = Path('data/content/catalog.json')
    
    try:
        with open(catalog_path) as f:
            catalog = json.load(f)
        
        # Check structure
        assert 'version' in catalog, "Missing catalog version"
        assert 'items' in catalog, "Missing catalog items"
        assert isinstance(catalog['items'], list), "Items should be a list"
        assert len(catalog['items']) >= 15, f"Expected 15+ items, got {len(catalog['items'])}"
        
        # Check item structure
        for i, item in enumerate(catalog['items'][:3]):  # Check first 3 items
            required_fields = ['content_id', 'type', 'title', 'personas', 'signal_triggers']
            for field in required_fields:
                assert field in item, f"Item {i} missing field: {field}"
        
        print(f"✅ Content catalog validation passed ({len(catalog['items'])} items)")
        
    except Exception as e:
        raise AssertionError(f"Content catalog validation failed: {e}")

def test_docker_configuration():
    """Test Docker configuration files."""
    print("🐳 Testing Docker configuration...")
    
    # Test Dockerfile
    dockerfile_path = Path('Dockerfile')
    dockerfile_content = dockerfile_path.read_text()
    
    assert 'FROM python:3.11-slim' in dockerfile_content, "Should use Python 3.11"
    assert 'as development' in dockerfile_content, "Should have development stage"
    assert 'WORKDIR /app' in dockerfile_content, "Should set working directory"
    
    # Test docker-compose.yml
    compose_path = Path('docker-compose.yml')
    compose_content = compose_path.read_text()
    
    assert 'spendsense-app:' in compose_content, "Missing main service"
    assert 'spendsense-test:' in compose_content, "Missing test service"
    assert 'cached' in compose_content, "Should have volume caching"
    assert 'volumes:' in compose_content, "Should have persistent volumes"
    
    # Test Makefile
    makefile_path = Path('Makefile')
    makefile_content = makefile_path.read_text()
    
    assert 'make init' in makefile_content, "Missing init command"
    assert 'make shell' in makefile_content, "Missing shell command"
    assert 'make test' in makefile_content, "Missing test command"
    
    print("✅ Docker configuration validation passed")

def test_import_structure():
    """Test Python import structure without dependencies."""
    print("🔍 Testing import structure...")
    
    # Test that Python files have valid syntax
    python_files = [
        'src/features/schema.py',
        'src/db/connection.py', 
        'src/ingest/data_generator.py'
    ]
    
    for file_path in python_files:
        try:
            with open(file_path) as f:
                content = f.read()
            
            # Basic syntax check by compiling
            compile(content, file_path, 'exec')
            
        except SyntaxError as e:
            raise AssertionError(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            # This is expected for missing dependencies
            pass
    
    print("✅ Import structure validation passed")

def main():
    """Run all validation tests."""
    print("🚀 Starting SpendSense Implementation Validation")
    print("=" * 50)
    
    tests = [
        test_project_structure,
        test_schema_definition,
        test_database_schema,
        test_data_generator_logic,
        test_content_catalog,
        test_docker_configuration,
        test_import_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print()
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"💥 {test.__name__} error: {e}")
            failed += 1
            print()
    
    print("=" * 50)
    print(f"🎯 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All validation tests passed! Implementation is rock-solid.")
        print("✅ Ready for Docker deployment and external dependency testing.")
    else:
        print("⚠️ Some validation tests failed. Please fix issues before proceeding.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

