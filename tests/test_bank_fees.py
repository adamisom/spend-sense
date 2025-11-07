"""
Tests for bank fee detection
"""
import pytest
import pandas as pd
from src.features.bank_fees import detect_bank_fees

class TestBankFeeDetection:
    """Test bank fee signal detection."""
    
    def test_empty_transactions(self):
        """Test that empty transactions return zeros."""
        result = detect_bank_fees(pd.DataFrame(), window_days=180)
        assert result['monthly_bank_fees'] == 0.0
        assert result['bank_fee_count'] == 0
        assert result['has_overdraft_fees'] is False
        assert result['has_atm_fees'] is False
        assert result['has_maintenance_fees'] is False
    
    def test_no_fees_detected(self):
        """Test transactions with no fees."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Grocery Store', 'amount': -50.0, 'category_primary': 'Groceries'},
            {'merchant_name': 'Gas Station', 'amount': -30.0, 'category_primary': 'Gas'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['monthly_bank_fees'] == 0.0
        assert result['bank_fee_count'] == 0
        assert all(not result[k] for k in ['has_overdraft_fees', 'has_atm_fees', 'has_maintenance_fees'])
    
    def test_overdraft_fee_detection(self):
        """Test overdraft fee detection via merchant name."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Bank Overdraft Fee', 'amount': -35.0, 'category_primary': 'Bank Fees'},
            {'merchant_name': 'NSF Charge', 'amount': -25.0, 'category_primary': 'Service Charge'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['has_overdraft_fees'] is True
        assert result['bank_fee_count'] == 2
        assert result['monthly_bank_fees'] > 0
    
    def test_atm_fee_detection_merchant(self):
        """Test ATM fee detection via merchant name."""
        transactions = pd.DataFrame([
            {'merchant_name': 'ATM Surcharge', 'amount': -3.00, 'category_primary': 'ATM Fee'},
            {'merchant_name': 'ATM Withdrawal Fee', 'amount': -2.50, 'category_primary': 'Bank Fees'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['has_atm_fees'] is True
        assert result['bank_fee_count'] == 2
    
    def test_atm_fee_detection_category(self):
        """Test ATM fee detection via category."""
        transactions = pd.DataFrame([
            {'merchant_name': 'ATM', 'amount': -3.00, 'category_primary': 'ATM Fee'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['has_atm_fees'] is True
    
    def test_maintenance_fee_detection(self):
        """Test maintenance fee detection."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Monthly Maintenance Fee', 'amount': -12.00, 'category_primary': 'Service Charge'},
            {'merchant_name': 'Account Fee', 'amount': -10.00, 'category_primary': 'Bank Fees'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['has_maintenance_fees'] is True
        assert result['bank_fee_count'] == 2
    
    def test_monthly_average_calculation(self):
        """Test monthly average calculation."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Bank Fee', 'amount': -20.0, 'category_primary': 'Bank Fees'},
            {'merchant_name': 'Service Charge', 'amount': -10.0, 'category_primary': 'Service Charge'},
        ])
        # 180 days = 6 months, so $30 total / 6 = $5/month
        result = detect_bank_fees(transactions, window_days=180)
        assert result['monthly_bank_fees'] == pytest.approx(5.0, abs=0.01)
    
    def test_monthly_average_30_days(self):
        """Test monthly average with 30-day window."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Bank Fee', 'amount': -30.0, 'category_primary': 'Bank Fees'},
        ])
        # 30 days = 1 month, so $30 / 1 = $30/month
        result = detect_bank_fees(transactions, window_days=30)
        assert result['monthly_bank_fees'] == pytest.approx(30.0, abs=0.01)
    
    def test_multiple_fee_types(self):
        """Test detection of multiple fee types in same dataset."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Overdraft Fee', 'amount': -35.0, 'category_primary': 'Bank Fees'},
            {'merchant_name': 'ATM Surcharge', 'amount': -3.0, 'category_primary': 'ATM Fee'},
            {'merchant_name': 'Monthly Fee', 'amount': -12.0, 'category_primary': 'Service Charge'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['has_overdraft_fees'] is True
        assert result['has_atm_fees'] is True
        assert result['has_maintenance_fees'] is True
        assert result['bank_fee_count'] == 3
    
    def test_positive_amounts_ignored(self):
        """Test that positive amounts (deposits) are not counted as fees."""
        transactions = pd.DataFrame([
            {'merchant_name': 'Bank Fee', 'amount': 20.0, 'category_primary': 'Bank Fees'},  # Positive = deposit
            {'merchant_name': 'Service Charge', 'amount': -10.0, 'category_primary': 'Service Charge'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        # Only negative amount should be counted
        assert result['bank_fee_count'] == 1
        assert result['monthly_bank_fees'] > 0
    
    def test_missing_merchant_name(self):
        """Test handling of missing merchant_name."""
        transactions = pd.DataFrame([
            {'merchant_name': None, 'amount': -35.0, 'category_primary': 'Bank Fees'},
            {'merchant_name': 'OD Fee', 'amount': -25.0, 'category_primary': 'Service Charge'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        # Should still detect fees via category
        assert result['bank_fee_count'] >= 1
    
    def test_case_insensitive_matching(self):
        """Test that fee detection is case-insensitive."""
        transactions = pd.DataFrame([
            {'merchant_name': 'OVERDRAFT FEE', 'amount': -35.0, 'category_primary': 'Bank Fees'},
            {'merchant_name': 'atm surcharge', 'amount': -3.0, 'category_primary': 'ATM Fee'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        assert result['has_overdraft_fees'] is True
        assert result['has_atm_fees'] is True
    
    def test_high_monthly_fees_threshold(self):
        """Test that high monthly fees are calculated correctly for Fee Fighter threshold."""
        # $20/month threshold for Fee Fighter
        # Over 180 days (6 months), need $120 total to average $20/month
        transactions = pd.DataFrame([
            {'merchant_name': 'Bank Fee', 'amount': -40.0, 'category_primary': 'Bank Fees'},
            {'merchant_name': 'Service Charge', 'amount': -40.0, 'category_primary': 'Service Charge'},
            {'merchant_name': 'ATM Fee', 'amount': -40.0, 'category_primary': 'ATM Fee'},
        ])
        result = detect_bank_fees(transactions, window_days=180)
        # $120 total / 6 months = $20/month
        assert result['monthly_bank_fees'] == pytest.approx(20.0, abs=0.01)

