"""
Transform transactions_formatted.csv schema to SpendSense schema
"""
import pandas as pd
from typing import Dict, Any, Optional
from loguru import logger


def transform_formatted_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform transactions_formatted.csv to SpendSense schema.
    
    Maps the new CSV format (with customer_id, merchant_id, etc.) to the
    existing SpendSense schema (with user_id, account_id, merchant_name, etc.).
    
    Args:
        df: DataFrame with transactions_formatted.csv schema
        
    Returns:
        DataFrame with SpendSense schema (compatible with existing transactions table)
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to transformer")
        return pd.DataFrame()
    
    transformed = pd.DataFrame()
    
    # Core field mappings
    transformed['transaction_id'] = df['transaction_id']
    
    # User/Account mapping
    # Assume customer_id maps to user_id, and create a default account_id
    transformed['user_id'] = df['customer_id']
    # Create account_id by appending '_checking' (could be enhanced to detect account type)
    transformed['account_id'] = df['customer_id'] + '_checking'
    
    # Date handling
    transformed['date'] = pd.to_datetime(df['date']).dt.date
    
    # Amount (already numeric)
    transformed['amount'] = df['amount']
    
    # Merchant mapping - use merchant_id as merchant_name (could be enhanced with lookup table)
    transformed['merchant_name'] = df['merchant_id']
    
    # Category mapping
    transformed['category_primary'] = df['merchant_category']
    transformed['category_detailed'] = df['merchant_category']  # Same value, could be enhanced
    
    # Payment method to payment_channel mapping
    payment_mapping = {
        'debit_card': 'in store',
        'credit_card': 'in store',
        'digital_wallet': 'online',
        'cash': 'other',
        'bank_transfer': 'other'
    }
    transformed['payment_channel'] = df['payment_method'].map(payment_mapping)
    
    # Status to pending boolean
    transformed['pending'] = df['status'] == 'pending'
    
    # New fraud detection fields (direct mapping)
    transformed['is_fraud'] = df['is_fraud'].astype(int)
    transformed['latitude'] = df['latitude']
    transformed['longitude'] = df['longitude']
    transformed['account_balance'] = df['account_balance']
    transformed['transaction_type'] = df['transaction_type']
    transformed['amount_category'] = df['amount_category']
    transformed['status'] = df['status']
    
    logger.info(f"Transformed {len(transformed)} transactions from formatted schema to SpendSense schema")
    
    return transformed


def validate_transformed_schema(df: pd.DataFrame) -> bool:
    """
    Validate that transformed DataFrame has required SpendSense schema columns.
    
    Args:
        df: Transformed DataFrame to validate
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_columns = [
        'transaction_id', 'account_id', 'user_id', 'date', 'amount',
        'merchant_name', 'category_primary', 'category_detailed',
        'payment_channel', 'pending'
    ]
    
    optional_columns = [
        'is_fraud', 'latitude', 'longitude', 'account_balance',
        'transaction_type', 'amount_category', 'status'
    ]
    
    missing_required = [col for col in required_columns if col not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")
    
    # Check for optional columns and warn if missing
    missing_optional = [col for col in optional_columns if col not in df.columns]
    if missing_optional:
        logger.warning(f"Missing optional fraud detection columns: {missing_optional}")
    
    return True


def load_and_transform_formatted_transactions(csv_path: str) -> pd.DataFrame:
    """
    Load transactions_formatted.csv and transform to SpendSense schema.
    
    Args:
        csv_path: Path to transactions_formatted.csv file
        
    Returns:
        Transformed DataFrame ready for database insertion
    """
    logger.info(f"Loading formatted transactions from {csv_path}")
    df = pd.read_csv(csv_path)
    
    logger.info(f"Loaded {len(df)} transactions from CSV")
    
    # Transform schema
    transformed = transform_formatted_transactions(df)
    
    # Validate
    validate_transformed_schema(transformed)
    
    return transformed

