#!/usr/bin/env python3
"""
Compute user signals for all users in the database
This script extracts signals from transactions and saves them to the database
"""
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
import sys
import sqlite3

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.features.bank_fees import detect_bank_fees
from src.features.fraud_detection import extract_fraud_signals


def compute_user_signals(user_id: str, window_days: int = 180, db_path: str = "db/spend_sense.db") -> UserSignals:
    """
    Compute all signals for a user from their transactions.
    
    Args:
        user_id: User identifier
        window_days: Number of days to look back
        db_path: Database path
        
    Returns:
        UserSignals object with computed signals
    """
    try:
        cutoff_date = (datetime.now() - timedelta(days=window_days)).date()
        
        with database_transaction(db_path) as conn:
            # Get transactions (include account_id for savings computation)
            # Check which columns exist (is_fraud may not exist in older schemas)
            try:
                # Try with all columns first
                transactions_df = pd.read_sql_query("""
                    SELECT 
                        transaction_id, account_id, date, amount, merchant_name, 
                        category_primary, category_detailed, payment_channel,
                        is_fraud, transaction_type, status
                    FROM transactions
                    WHERE user_id = ? AND date >= ?
                    ORDER BY date DESC
                """, conn, params=(user_id, cutoff_date))
            except sqlite3.OperationalError:
                # Fallback if is_fraud column doesn't exist
                transactions_df = pd.read_sql_query("""
                    SELECT 
                        transaction_id, account_id, date, amount, merchant_name, 
                        category_primary, category_detailed, payment_channel
                    FROM transactions
                    WHERE user_id = ? AND date >= ?
                    ORDER BY date DESC
                """, conn, params=(user_id, cutoff_date))
                # Add missing columns with defaults
                transactions_df['is_fraud'] = 0
                transactions_df['transaction_type'] = None
                transactions_df['status'] = None
            
            # Get accounts
            accounts_df = pd.read_sql_query("""
                SELECT account_id, type, subtype, current_balance, credit_limit
                FROM accounts
                WHERE user_id = ?
            """, conn, params=(user_id,))
            
            # Get liabilities
            liabilities_df = pd.read_sql_query("""
                SELECT account_id, apr_percentage, is_overdue, 
                       minimum_payment_amount, last_payment_amount
                FROM liabilities
                WHERE account_id IN (SELECT account_id FROM accounts WHERE user_id = ?)
            """, conn, params=(user_id,))
        
        # Initialize signals with defaults
        signals_dict = {
            'window': f'{window_days}d',
            'computed_at': datetime.now(),
            'computation_errors': []
        }
        
        # Compute credit signals
        try:
            credit_signals = compute_credit_signals(accounts_df, liabilities_df, transactions_df)
            signals_dict.update(credit_signals)
        except Exception as e:
            logger.warning(f"Error computing credit signals for {user_id}: {e}")
            signals_dict['computation_errors'].append(f"Credit signals: {str(e)}")
        
        # Compute income signals
        try:
            income_signals = compute_income_signals(transactions_df, window_days)
            signals_dict.update(income_signals)
        except Exception as e:
            logger.warning(f"Error computing income signals for {user_id}: {e}")
            signals_dict['computation_errors'].append(f"Income signals: {str(e)}")
        
        # Compute subscription signals
        try:
            subscription_signals = compute_subscription_signals(transactions_df, window_days)
            signals_dict.update(subscription_signals)
        except Exception as e:
            logger.warning(f"Error computing subscription signals for {user_id}: {e}")
            signals_dict['computation_errors'].append(f"Subscription signals: {str(e)}")
        
        # Compute savings signals
        try:
            savings_signals = compute_savings_signals(transactions_df, accounts_df, window_days)
            signals_dict.update(savings_signals)
        except Exception as e:
            logger.warning(f"Error computing savings signals for {user_id}: {e}")
            signals_dict['computation_errors'].append(f"Savings signals: {str(e)}")
        
        # Compute bank fee signals
        try:
            bank_fee_signals = detect_bank_fees(transactions_df, window_days)
            signals_dict.update(bank_fee_signals)
        except Exception as e:
            logger.warning(f"Error computing bank fee signals for {user_id}: {e}")
            signals_dict['computation_errors'].append(f"Bank fee signals: {str(e)}")
        
        # Compute fraud signals
        try:
            fraud_signals = extract_fraud_signals(transactions_df)
            signals_dict.update(fraud_signals)
        except Exception as e:
            logger.warning(f"Error computing fraud signals for {user_id}: {e}")
            signals_dict['computation_errors'].append(f"Fraud signals: {str(e)}")
        
        # Compute data quality score
        signals_dict['data_quality_score'] = compute_data_quality_score(signals_dict, transactions_df)
        signals_dict['insufficient_data'] = signals_dict['data_quality_score'] < 0.1
        
        # Create UserSignals object
        signals = UserSignals(**signals_dict)
        
        return signals
        
    except Exception as e:
        logger.error(f"Error computing signals for {user_id}: {e}")
        # Return minimal signals with error
        return UserSignals(
            window=f'{window_days}d',
            computation_errors=[f"Signal computation failed: {str(e)}"],
            data_quality_score=0.0,
            insufficient_data=True
        )


def compute_credit_signals(accounts_df: pd.DataFrame, liabilities_df: pd.DataFrame, transactions_df: pd.DataFrame) -> dict:
    """Compute credit-related signals."""
    signals = {
        'credit_utilization_max': None,
        'has_interest_charges': False,
        'is_overdue': False,
        'minimum_payment_only': False
    }
    
    if liabilities_df.empty:
        return signals
    
    # Credit utilization
    credit_accounts = accounts_df[accounts_df['subtype'] == 'credit card']
    if not credit_accounts.empty:
        utilizations = []
        for _, account in credit_accounts.iterrows():
            if account.get('credit_limit') and account.get('credit_limit') > 0:
                balance = account.get('current_balance', 0) or 0
                utilization = balance / account['credit_limit']
                utilizations.append(utilization)
        
        if utilizations:
            signals['credit_utilization_max'] = max(utilizations)
    
    # Interest charges and overdue
    if not liabilities_df.empty:
        signals['has_interest_charges'] = (liabilities_df['apr_percentage'] > 0).any()
        signals['is_overdue'] = liabilities_df['is_overdue'].any() if 'is_overdue' in liabilities_df.columns else False
    
    # Minimum payment only (simplified - would need payment history)
    signals['minimum_payment_only'] = False
    
    return signals


def compute_income_signals(transactions_df: pd.DataFrame, window_days: int) -> dict:
    """Compute income-related signals."""
    signals = {
        'income_pay_gap': None,
        'cash_flow_buffer': None,
        'income_variability': None
    }
    
    if transactions_df.empty:
        return signals
    
    # Income transactions (positive amounts, payroll category)
    income_txns = transactions_df[
        (transactions_df['amount'] > 0) &
        (transactions_df['category_primary'].str.contains('Payroll|Deposit|Income', case=False, na=False))
    ]
    
    if len(income_txns) >= 2:
        income_txns = income_txns.sort_values('date')
        income_dates = pd.to_datetime(income_txns['date']).dt.date
        
        # Income pay gap (days between deposits)
        gaps = [(income_dates.iloc[i] - income_dates.iloc[i-1]).days 
                for i in range(1, len(income_dates))]
        if gaps:
            signals['income_pay_gap'] = int(sum(gaps) / len(gaps))
        
        # Income variability (coefficient of variation)
        amounts = income_txns['amount'].values
        if len(amounts) > 1 and amounts.mean() > 0:
            signals['income_variability'] = float(amounts.std() / amounts.mean())
    
    # Cash flow buffer (simplified - would need expense calculation)
    signals['cash_flow_buffer'] = None
    
    return signals


def compute_subscription_signals(transactions_df: pd.DataFrame, window_days: int) -> dict:
    """Compute subscription-related signals."""
    signals = {
        'subscription_count': 0,
        'monthly_subscription_spend': 0.0,
        'subscription_share': 0.0
    }
    
    if transactions_df.empty:
        return signals
    
    # Subscription transactions (recurring, subscription category)
    subscription_txns = transactions_df[
        (transactions_df['category_primary'].str.contains('Subscription|Recurring', case=False, na=False)) |
        (transactions_df['category_detailed'].str.contains('Subscription', case=False, na=False))
    ]
    
    # Count unique subscriptions (by merchant)
    if not subscription_txns.empty:
        unique_subscriptions = subscription_txns['merchant_name'].nunique()
        signals['subscription_count'] = int(unique_subscriptions)
        
        # Monthly spend
        monthly_spend = subscription_txns['amount'].abs().sum() / (window_days / 30.0)
        signals['monthly_subscription_spend'] = float(monthly_spend)
        
        # Subscription share
        total_spend = transactions_df[transactions_df['amount'] < 0]['amount'].abs().sum()
        if total_spend > 0:
            signals['subscription_share'] = float(subscription_txns['amount'].abs().sum() / total_spend)
    
    return signals


def compute_savings_signals(transactions_df: pd.DataFrame, accounts_df: pd.DataFrame, window_days: int) -> dict:
    """Compute savings-related signals."""
    signals = {
        'savings_growth_rate': None,
        'monthly_savings_inflow': 0.0,
        'emergency_fund_months': None
    }
    
    if transactions_df.empty:
        return signals
    
    # Savings account transactions
    savings_accounts = accounts_df[accounts_df['subtype'] == 'savings']
    if not savings_accounts.empty:
        savings_account_ids = savings_accounts['account_id'].tolist()
        savings_txns = transactions_df[transactions_df['account_id'].isin(savings_account_ids)]
        
        # Savings deposits (positive amounts)
        deposits = savings_txns[savings_txns['amount'] > 0]
        if not deposits.empty:
            monthly_inflow = deposits['amount'].sum() / (window_days / 30.0)
            signals['monthly_savings_inflow'] = float(monthly_inflow)
    
    return signals


def compute_data_quality_score(signals_dict: dict, transactions_df: pd.DataFrame) -> float:
    """Compute data quality score based on available data."""
    score = 1.0
    
    # Penalize for missing transactions
    if transactions_df.empty:
        score *= 0.1
    elif len(transactions_df) < 10:
        score *= 0.5
    elif len(transactions_df) < 30:
        score *= 0.7
    
    # Penalize for computation errors
    errors = signals_dict.get('computation_errors', [])
    if errors:
        score *= max(0.1, 1.0 - (len(errors) * 0.1))
    
    # Penalize for missing critical signals
    if signals_dict.get('credit_utilization_max') is None and signals_dict.get('monthly_savings_inflow', 0) == 0:
        score *= 0.8
    
    return max(0.0, min(1.0, score))


def compute_all_user_signals(window_days: int = 180, db_path: str = "db/spend_sense.db", limit: int = None):
    """Compute signals for all users in the database."""
    try:
        with database_transaction(db_path) as conn:
            # Get all user IDs
            query = "SELECT DISTINCT user_id FROM users"
            if limit:
                query += f" LIMIT {limit}"
            users = conn.execute(query).fetchall()
        
        total_users = len(users)
        logger.info(f"Computing signals for {total_users} users...")
        
        success_count = 0
        error_count = 0
        
        for idx, row in enumerate(users, 1):
            user_id = row['user_id']
            try:
                logger.info(f"[{idx}/{total_users}] Computing signals for {user_id}...")
                signals = compute_user_signals(user_id, window_days, db_path)
                
                # Save to database
                signals_dict = signals.model_dump()
                save_user_signals(user_id, f'{window_days}d', signals_dict, db_path)
                
                success_count += 1
                logger.info(f"✅ Saved signals for {user_id} (quality: {signals.data_quality_score:.2f})")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error computing signals for {user_id}: {e}")
        
        logger.info(f"\n✅ Signal computation complete!")
        logger.info(f"   Success: {success_count}/{total_users}")
        logger.info(f"   Errors: {error_count}/{total_users}")
        
        return success_count, error_count
        
    except Exception as e:
        logger.error(f"Error computing signals: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compute user signals from transactions')
    parser.add_argument('--window-days', type=int, default=180, help='Time window in days (default: 180)')
    parser.add_argument('--db-path', default='db/spend_sense.db', help='Database path')
    parser.add_argument('--limit', type=int, help='Limit number of users to process')
    parser.add_argument('--user-id', help='Compute signals for a single user')
    
    args = parser.parse_args()
    
    try:
        if args.user_id:
            logger.info(f"Computing signals for user {args.user_id}...")
            signals = compute_user_signals(args.user_id, args.window_days, args.db_path)
            signals_dict = signals.model_dump()
            save_user_signals(args.user_id, f'{args.window_days}d', signals_dict, args.db_path)
            logger.info(f"✅ Signals computed and saved for {args.user_id}")
            logger.info(f"   Data quality: {signals.data_quality_score:.2f}")
        else:
            compute_all_user_signals(args.window_days, args.db_path, args.limit)
            
    except Exception as e:
        logger.error(f"Signal computation failed: {e}")
        sys.exit(1)

