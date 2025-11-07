"""
Bank fee signal detection
Detects overdraft fees, ATM fees, maintenance fees from transactions
"""
import pandas as pd
from typing import Dict
from loguru import logger

def detect_bank_fees(transactions: pd.DataFrame, window_days: int = 180) -> Dict:
    """Detect bank fees from transaction data.
    
    Args:
        transactions: DataFrame with transaction data
        window_days: Number of days in analysis window
        
    Returns:
        Dictionary with bank fee signals
    """
    if transactions.empty:
        return {
            'monthly_bank_fees': 0.0,
            'bank_fee_count': 0,
            'has_overdraft_fees': False,
            'has_atm_fees': False,
            'has_maintenance_fees': False
        }
    
    # Fee categories (adjust based on your transaction categories)
    fee_keywords = {
        'overdraft': ['overdraft', 'od fee', 'nsf', 'insufficient funds'],
        'atm': ['atm fee', 'atm surcharge', 'atm withdrawal fee'],
        'maintenance': ['maintenance fee', 'monthly fee', 'service charge', 'account fee']
    }
    
    # Convert merchant_name and category to lowercase for matching
    transactions_lower = transactions.copy()
    transactions_lower['merchant_lower'] = transactions_lower['merchant_name'].str.lower().fillna('')
    transactions_lower['category_lower'] = transactions_lower['category_primary'].str.lower().fillna('')
    
    # Detect fee transactions
    fee_transactions = transactions_lower[
        (transactions_lower['amount'] < 0) &  # Fees are negative
        (
            transactions_lower['category_primary'].isin(['Bank Fees', 'Service Charge', 'ATM Fee']) |
            transactions_lower['merchant_lower'].str.contains('fee|charge|overdraft', case=False, na=False)
        )
    ]
    
    if fee_transactions.empty:
        return {
            'monthly_bank_fees': 0.0,
            'bank_fee_count': 0,
            'has_overdraft_fees': False,
            'has_atm_fees': False,
            'has_maintenance_fees': False
        }
    
    # Calculate monthly average
    total_fees = abs(fee_transactions['amount'].sum())
    months_in_window = window_days / 30.0
    monthly_fees = total_fees / months_in_window if months_in_window > 0 else 0.0
    
    # Detect specific fee types
    has_overdraft = fee_transactions['merchant_lower'].str.contains(
        '|'.join(fee_keywords['overdraft']), case=False, na=False
    ).any()
    
    has_atm = fee_transactions['merchant_lower'].str.contains(
        '|'.join(fee_keywords['atm']), case=False, na=False
    ).any() or fee_transactions['category_lower'].str.contains('atm', case=False, na=False).any()
    
    has_maintenance = fee_transactions['merchant_lower'].str.contains(
        '|'.join(fee_keywords['maintenance']), case=False, na=False
    ).any()
    
    return {
        'monthly_bank_fees': round(monthly_fees, 2),
        'bank_fee_count': len(fee_transactions),
        'has_overdraft_fees': bool(has_overdraft),
        'has_atm_fees': bool(has_atm),
        'has_maintenance_fees': bool(has_maintenance)
    }

