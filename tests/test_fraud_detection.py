"""
Tests for fraud detection functionality
"""
import pytest
import pandas as pd
from src.features.fraud_detection import (
    extract_fraud_signals,
    calculate_fraud_risk_score,
    get_fraud_transactions,
    analyze_fraud_patterns
)


class TestFraudDetection:
    """Test fraud detection signal extraction."""
    
    def test_fraud_signal_extraction_no_fraud(self):
        """Test fraud signal extraction with no fraud."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2', 'T3'],
            'is_fraud': [0, 0, 0],
            'amount': [100, 50, 200]
        })
        
        signals = extract_fraud_signals(transactions)
        
        assert signals['fraud_transaction_count'] == 0
        assert signals['fraud_rate'] == 0.0
        assert signals['has_fraud_history'] == False
        assert signals['fraud_risk_score'] == 0.0
    
    def test_fraud_signal_extraction_with_fraud(self):
        """Test fraud signal extraction with fraud transactions."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2', 'T3'],
            'is_fraud': [0, 1, 0],
            'amount': [100, 50, 200]
        })
        
        signals = extract_fraud_signals(transactions)
        
        assert signals['fraud_transaction_count'] == 1
        assert signals['fraud_rate'] == pytest.approx(1/3)
        assert signals['has_fraud_history'] == True
        assert signals['fraud_risk_score'] > 0
    
    def test_fraud_signal_extraction_missing_column(self):
        """Test fraud signal extraction when is_fraud column is missing."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2'],
            'amount': [100, 50]
        })
        
        signals = extract_fraud_signals(transactions)
        
        assert signals['fraud_transaction_count'] == 0
        assert signals['fraud_rate'] == 0.0
        assert signals['has_fraud_history'] == False
        assert signals['fraud_risk_score'] == 0.0
    
    def test_fraud_signal_extraction_empty_dataframe(self):
        """Test fraud signal extraction with empty DataFrame."""
        transactions = pd.DataFrame()
        
        signals = extract_fraud_signals(transactions)
        
        assert signals['fraud_transaction_count'] == 0
        assert signals['fraud_rate'] == 0.0
        assert signals['has_fraud_history'] == False
        assert signals['fraud_risk_score'] == 0.0
    
    def test_calculate_fraud_risk_score_no_fraud(self):
        """Test fraud risk score calculation with no fraud."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2'],
            'is_fraud': [0, 0]
        })
        
        score = calculate_fraud_risk_score(transactions, 0, 0.0)
        assert score == 0.0
    
    def test_calculate_fraud_risk_score_with_fraud(self):
        """Test fraud risk score calculation with fraud."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2', 'T3'],
            'is_fraud': [0, 1, 0],
            'status': ['approved', 'declined', 'approved'],
            'transaction_type': ['purchase', 'transfer', 'purchase']
        })
        
        score = calculate_fraud_risk_score(transactions, 1, 1/3)
        assert score > 0
        assert score <= 1.0
    
    def test_get_fraud_transactions(self):
        """Test getting fraud transactions from DataFrame."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2', 'T3', 'T4'],
            'is_fraud': [0, 1, 0, 1],
            'amount': [100, 50, 200, 75]
        })
        
        fraud_transactions = get_fraud_transactions(transactions)
        
        assert len(fraud_transactions) == 2
        assert all(fraud_transactions['is_fraud'] == 1)
        assert list(fraud_transactions['transaction_id']) == ['T2', 'T4']
    
    def test_get_fraud_transactions_no_fraud(self):
        """Test getting fraud transactions when none exist."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2'],
            'is_fraud': [0, 0]
        })
        
        fraud_transactions = get_fraud_transactions(transactions)
        assert len(fraud_transactions) == 0
    
    def test_analyze_fraud_patterns(self):
        """Test fraud pattern analysis."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2', 'T3'],
            'is_fraud': [0, 1, 1],
            'payment_method': ['credit_card', 'credit_card', 'debit_card'],
            'merchant_category': ['retail', 'retail', 'transportation'],
            'transaction_type': ['purchase', 'purchase', 'transfer'],
            'status': ['approved', 'approved', 'declined'],
            'amount': [100, 50, 200]
        })
        
        patterns = analyze_fraud_patterns(transactions)
        
        assert patterns['total_fraud'] == 2
        assert 'patterns' in patterns
        assert 'payment_method' in patterns['patterns']
        assert 'merchant_category' in patterns['patterns']
        assert 'transaction_type' in patterns['patterns']
        assert 'status' in patterns['patterns']
        assert 'amount_stats' in patterns['patterns']
    
    def test_analyze_fraud_patterns_no_fraud(self):
        """Test fraud pattern analysis with no fraud."""
        transactions = pd.DataFrame({
            'transaction_id': ['T1', 'T2'],
            'is_fraud': [0, 0]
        })
        
        patterns = analyze_fraud_patterns(transactions)
        
        assert patterns['total_fraud'] == 0
        assert patterns['patterns'] == {}

