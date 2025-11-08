"""
Extract fraud-related signals from transactions
"""
from typing import Dict, Any, Optional
import pandas as pd
from loguru import logger


def extract_fraud_signals(transactions: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract fraud-related signals from transactions.
    
    Args:
        transactions: DataFrame with transaction data including is_fraud column
        
    Returns:
        Dictionary with fraud signals:
        - fraud_transaction_count: Number of fraud transactions
        - fraud_rate: Fraction of transactions that are fraud
        - has_fraud_history: Boolean indicating if user has fraud
        - fraud_risk_score: Risk score (0.0-1.0) based on fraud patterns
    """
    if transactions.empty:
        return {
            'fraud_transaction_count': 0,
            'fraud_rate': 0.0,
            'has_fraud_history': False,
            'fraud_risk_score': 0.0
        }
    
    # Check if is_fraud column exists
    if 'is_fraud' not in transactions.columns:
        logger.warning("is_fraud column not found in transactions, returning zero fraud signals")
        return {
            'fraud_transaction_count': 0,
            'fraud_rate': 0.0,
            'has_fraud_history': False,
            'fraud_risk_score': 0.0
        }
    
    # Calculate basic fraud metrics
    fraud_count = int(transactions['is_fraud'].sum())
    total_count = len(transactions)
    fraud_rate = float(fraud_count / total_count) if total_count > 0 else 0.0
    has_fraud_history = fraud_count > 0
    
    # Calculate fraud risk score
    # Base score on fraud rate, but also consider other factors
    risk_score = calculate_fraud_risk_score(transactions, fraud_count, fraud_rate)
    
    return {
        'fraud_transaction_count': fraud_count,
        'fraud_rate': fraud_rate,
        'has_fraud_history': has_fraud_history,
        'fraud_risk_score': risk_score
    }


def calculate_fraud_risk_score(
    transactions: pd.DataFrame,
    fraud_count: int,
    fraud_rate: float
) -> float:
    """
    Calculate fraud risk score based on multiple factors.
    
    Args:
        transactions: DataFrame with transaction data
        fraud_count: Number of fraud transactions
        fraud_rate: Fraction of transactions that are fraud
        
    Returns:
        Risk score between 0.0 and 1.0
    """
    if fraud_count == 0:
        return 0.0
    
    # Base score from fraud rate (scaled)
    base_score = min(fraud_rate * 10, 1.0)  # Scale fraud rate to 0-1
    
    # Additional risk factors
    risk_factors = []
    
    # Factor 1: Multiple fraud transactions indicate higher risk
    if fraud_count > 1:
        risk_factors.append(0.1 * min(fraud_count / 5, 1.0))  # Cap at 0.1
    
    # Factor 2: Check for declined fraud transactions (caught fraud)
    if 'status' in transactions.columns:
        fraud_transactions = transactions[transactions['is_fraud'] == 1]
        if not fraud_transactions.empty:
            declined_fraud = (fraud_transactions['status'] == 'declined').sum()
            if declined_fraud > 0:
                # Declined fraud suggests detection, but still indicates risk
                risk_factors.append(0.05)
    
    # Factor 3: Check for unusual patterns in fraud transactions
    if 'transaction_type' in transactions.columns:
        fraud_transactions = transactions[transactions['is_fraud'] == 1]
        if not fraud_transactions.empty:
            # Transfers and refunds in fraud might indicate higher risk
            high_risk_types = ['transfer', 'refund']
            high_risk_count = fraud_transactions['transaction_type'].isin(high_risk_types).sum()
            if high_risk_count > 0:
                risk_factors.append(0.05 * min(high_risk_count / fraud_count, 1.0))
    
    # Combine base score with risk factors
    total_score = base_score + sum(risk_factors)
    
    # Cap at 1.0
    return min(total_score, 1.0)


def get_fraud_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Get all fraud transactions from a DataFrame.
    
    Args:
        transactions: DataFrame with transaction data
        
    Returns:
        DataFrame containing only fraud transactions
    """
    if 'is_fraud' not in transactions.columns:
        logger.warning("is_fraud column not found, returning empty DataFrame")
        return pd.DataFrame()
    
    return transactions[transactions['is_fraud'] == 1].copy()


def analyze_fraud_patterns(transactions: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze patterns in fraud transactions.
    
    Args:
        transactions: DataFrame with transaction data including is_fraud column
        
    Returns:
        Dictionary with fraud pattern analysis
    """
    fraud_transactions = get_fraud_transactions(transactions)
    
    if fraud_transactions.empty:
        return {
            'total_fraud': 0,
            'patterns': {}
        }
    
    patterns = {}
    
    # Payment method patterns
    if 'payment_method' in fraud_transactions.columns:
        patterns['payment_method'] = fraud_transactions['payment_method'].value_counts().to_dict()
    
    # Merchant category patterns
    if 'merchant_category' in fraud_transactions.columns:
        patterns['merchant_category'] = fraud_transactions['merchant_category'].value_counts().to_dict()
    
    # Transaction type patterns
    if 'transaction_type' in fraud_transactions.columns:
        patterns['transaction_type'] = fraud_transactions['transaction_type'].value_counts().to_dict()
    
    # Status patterns
    if 'status' in fraud_transactions.columns:
        patterns['status'] = fraud_transactions['status'].value_counts().to_dict()
    
    # Amount statistics
    if 'amount' in fraud_transactions.columns:
        patterns['amount_stats'] = {
            'mean': float(fraud_transactions['amount'].abs().mean()),
            'median': float(fraud_transactions['amount'].abs().median()),
            'min': float(fraud_transactions['amount'].abs().min()),
            'max': float(fraud_transactions['amount'].abs().max())
        }
    
    return {
        'total_fraud': len(fraud_transactions),
        'patterns': patterns
    }

