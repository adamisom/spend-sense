"""
Synthetic data generator for SpendSense
Creates realistic financial data with edge cases for robust testing
"""
import random
import csv
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from faker import Faker
from loguru import logger
import pandas as pd

@dataclass
class UserProfile:
    """Represents a synthetic user's financial profile."""
    user_id: str
    income_level: str  # low, medium, high
    credit_behavior: str  # excellent, good, fair, poor
    savings_behavior: str  # aggressive, moderate, minimal, none
    subscription_tendency: str  # heavy, moderate, light
    financial_stress: bool
    scenario: Optional[str] = None  # For edge cases

class SyntheticDataGenerator:
    """Generate realistic synthetic financial data for testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with reproducible seed."""
        self.seed = seed
        random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)
        
        # Configuration
        self.income_ranges = {
            'low': (25000, 40000),
            'medium': (40000, 80000),
            'high': (80000, 150000)
        }
        
        self.merchant_categories = {
            'subscription': ['Netflix', 'Spotify', 'Disney+', 'Adobe', 'Zoom', 'NYTimes', 'Gym Membership'],
            'grocery': ['Whole Foods', 'Safeway', 'Trader Joes', 'Kroger', 'Costco'],
            'gas': ['Shell', 'Chevron', 'BP', 'Exxon', 'Arco'],
            'restaurant': ['Starbucks', 'McDonalds', 'Chipotle', 'Subway', 'Pizza Hut'],
            'shopping': ['Amazon', 'Target', 'Walmart', 'Best Buy', 'Apple Store'],
            'utilities': ['PG&E', 'AT&T', 'Comcast', 'Water Dept', 'Electric Co']
        }
        
        self.account_types = {
            'checking': {'balance_range': (500, 15000), 'typical_transactions': 50},
            'savings': {'balance_range': (0, 50000), 'typical_transactions': 5},
            'credit_card': {'balance_range': (0, 25000), 'credit_limit_range': (1000, 50000), 'typical_transactions': 20}
        }
        
    def generate_user_profiles(self, count: int, include_edge_cases: bool = True) -> List[UserProfile]:
        """Generate diverse user profiles including edge cases."""
        profiles = []
        
        # Generate diverse personas explicitly
        persona_profiles = [
            # High Utilization (5 users)
            *[UserProfile(f"user_{i+1:03d}", 'medium', 'poor', 'none', 'moderate', True, 'high_utilization') for i in range(5)],
            # Variable Income (5 users)  
            *[UserProfile(f"user_{i+6:03d}", 'low', 'fair', 'minimal', 'light', True, 'variable_income') for i in range(5)],
            # Subscription Heavy (5 users)
            *[UserProfile(f"user_{i+11:03d}", 'medium', 'good', 'moderate', 'heavy', False, 'subscription_heavy') for i in range(5)],
            # Savings Builder (5 users)
            *[UserProfile(f"user_{i+16:03d}", 'high', 'excellent', 'aggressive', 'light', False, 'savings_builder') for i in range(5)],
            # Fee Fighter (5 users)
            *[UserProfile(f"user_{i+21:03d}", 'low', 'fair', 'minimal', 'moderate', True, 'fee_fighter') for i in range(5)],
            # Mixed/Other (5 users)
            *[UserProfile(f"user_{i+26:03d}", 
                random.choices(['low', 'medium', 'high'], weights=[30, 50, 20])[0],
                random.choices(['excellent', 'good', 'fair', 'poor'], weights=[20, 40, 25, 15])[0],
                random.choices(['aggressive', 'moderate', 'minimal', 'none'], weights=[15, 35, 35, 15])[0],
                random.choices(['heavy', 'moderate', 'light'], weights=[20, 60, 20])[0],
                random.choice([True, False]),
                None) for i in range(5)]
        ]
        
        profiles.extend(persona_profiles[:count])
        
        return profiles
    
    def _generate_edge_case_profiles(self, count: int, start_idx: int) -> List[UserProfile]:
        """Generate specific edge case profiles for testing."""
        edge_cases = []
        scenarios = [
            'high_utilization_and_subscription_heavy',
            'sparse_transaction_history', 
            'high_savings_rate',
            'multiple_red_flags',
            'new_user_insufficient_data',
            'variable_income_gig_worker',
            'debt_consolidation_candidate',
            'cash_heavy_user'
        ]
        
        for i in range(count):
            scenario = scenarios[i % len(scenarios)]
            
            if scenario == 'high_utilization_and_subscription_heavy':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='medium',
                    credit_behavior='poor',  # High utilization
                    savings_behavior='none',
                    subscription_tendency='heavy',  # Many subscriptions
                    financial_stress=True,
                    scenario=scenario
                )
            elif scenario == 'sparse_transaction_history':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='low',
                    credit_behavior='excellent',
                    savings_behavior='minimal',
                    subscription_tendency='light',
                    financial_stress=False,
                    scenario=scenario
                )
            elif scenario == 'high_savings_rate':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='high',
                    credit_behavior='excellent',
                    savings_behavior='aggressive',
                    subscription_tendency='light',
                    financial_stress=False,
                    scenario=scenario
                )
            elif scenario == 'multiple_red_flags':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='low',
                    credit_behavior='poor',
                    savings_behavior='none',
                    subscription_tendency='heavy',
                    financial_stress=True,
                    scenario=scenario
                )
            elif scenario == 'new_user_insufficient_data':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='medium',
                    credit_behavior='good',
                    savings_behavior='moderate',
                    subscription_tendency='moderate',
                    financial_stress=False,
                    scenario=scenario
                )
            else:
                # Generate other edge cases
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level=random.choice(['low', 'medium', 'high']),
                    credit_behavior=random.choice(['excellent', 'good', 'fair', 'poor']),
                    savings_behavior=random.choice(['aggressive', 'moderate', 'minimal', 'none']),
                    subscription_tendency=random.choice(['heavy', 'moderate', 'light']),
                    financial_stress=random.choice([True, False]),
                    scenario=scenario
                )
            
            edge_cases.append(profile)
        
        return edge_cases
    
    def generate_users_csv(self, profiles: List[UserProfile]) -> List[Dict[str, Any]]:
        """Generate users CSV data."""
        users = []
        for profile in profiles:
            user = {
                'user_id': profile.user_id,
                'created_at': self.fake.date_time_between(start_date='-2y', end_date='now').isoformat(),
                'consent_status': True,  # All synthetic users consent
                'consent_date': self.fake.date_time_between(start_date='-1y', end_date='now').isoformat()
            }
            users.append(user)
        return users
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, output_dir: str = "data/synthetic"):
        """Save data to CSV file."""
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        
        if data:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Saved {len(data)} records to {filepath}")
        else:
            logger.warning(f"No data to save for {filename}")
    
    def generate_accounts_for_user(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """Generate accounts for a single user based on their profile."""
        accounts = []
        base_date = self.fake.date_between(start_date='-2y', end_date='-6m')
        
        # Every user gets a checking account
        checking_balance = random.uniform(*self.account_types['checking']['balance_range'])
        if profile.income_level == 'low':
            checking_balance *= 0.5
        elif profile.income_level == 'high':
            checking_balance *= 2.0
        
        accounts.append({
            'account_id': f"{profile.user_id}_checking",
            'user_id': profile.user_id,
            'type': 'depository',
            'subtype': 'checking',
            'available_balance': round(checking_balance, 2),
            'current_balance': round(checking_balance, 2),
            'credit_limit': None,
            'iso_currency_code': 'USD'
        })
        
        # Add savings account based on savings behavior
        if profile.savings_behavior != 'none':
            savings_balance = 0
            if profile.savings_behavior == 'aggressive':
                savings_balance = random.uniform(5000, 50000)
            elif profile.savings_behavior == 'moderate':
                savings_balance = random.uniform(1000, 15000)
            elif profile.savings_behavior == 'minimal':
                savings_balance = random.uniform(0, 5000)
            
            # Adjust for income level
            if profile.income_level == 'low':
                savings_balance *= 0.3
            elif profile.income_level == 'high':
                savings_balance *= 2.0
            
            # Handle edge cases
            if profile.scenario == 'high_savings_rate':
                savings_balance = random.uniform(25000, 100000)
            elif profile.scenario == 'multiple_red_flags':
                savings_balance = 0
            
            accounts.append({
                'account_id': f"{profile.user_id}_savings",
                'user_id': profile.user_id,
                'type': 'depository',
                'subtype': 'savings',
                'available_balance': round(savings_balance, 2),
                'current_balance': round(savings_balance, 2),
                'credit_limit': None,
                'iso_currency_code': 'USD'
            })
        
        # Add credit card accounts
        credit_card_count = 0
        if profile.credit_behavior in ['excellent', 'good']:
            credit_card_count = random.choice([1, 2, 3])
        elif profile.credit_behavior == 'fair':
            credit_card_count = random.choice([1, 2])
        elif profile.credit_behavior == 'poor':
            credit_card_count = random.choice([0, 1, 2])
        
        # Edge case adjustments
        if profile.scenario == 'high_utilization_and_subscription_heavy':
            credit_card_count = max(2, credit_card_count)
        elif profile.scenario == 'sparse_transaction_history':
            credit_card_count = min(1, credit_card_count)
        
        for i in range(credit_card_count):
            # Credit limit based on income and credit behavior
            base_limit = random.uniform(1000, 15000)
            if profile.income_level == 'high':
                base_limit *= 3
            elif profile.income_level == 'low':
                base_limit *= 0.5
            
            if profile.credit_behavior == 'excellent':
                base_limit *= 2
            elif profile.credit_behavior == 'poor':
                base_limit *= 0.5
            
            credit_limit = round(base_limit, 2)
            
            # Current balance (utilization) - based on scenario/persona
            if profile.scenario == 'high_utilization':
                utilization = random.uniform(0.6, 0.9)  # High utilization
            elif profile.scenario == 'savings_builder':
                utilization = random.uniform(0.0, 0.2)  # Low utilization
            elif profile.scenario == 'variable_income':
                utilization = random.uniform(0.3, 0.6)  # Moderate
            elif profile.scenario == 'subscription_heavy':
                utilization = random.uniform(0.4, 0.7)  # Moderate-high
            elif profile.scenario == 'fee_fighter':
                utilization = random.uniform(0.2, 0.5)  # Low-moderate
            elif profile.credit_behavior == 'poor' or profile.scenario == 'high_utilization_and_subscription_heavy':
                utilization = random.uniform(0.7, 0.95)  # High utilization
            elif profile.credit_behavior == 'fair':
                utilization = random.uniform(0.3, 0.7)
            else:
                utilization = random.uniform(0.05, 0.3)  # Low utilization
            
            # Special case handling
            if profile.scenario == 'multiple_red_flags':
                utilization = random.uniform(0.85, 0.98)
            elif profile.scenario == 'high_savings_rate':
                utilization = random.uniform(0.0, 0.1)
            
            current_balance = round(credit_limit * utilization, 2)
            
            accounts.append({
                'account_id': f"{profile.user_id}_credit_{i+1}",
                'user_id': profile.user_id,
                'type': 'credit',
                'subtype': 'credit card', 
                'available_balance': round(credit_limit - current_balance, 2),
                'current_balance': current_balance,
                'credit_limit': credit_limit,
                'iso_currency_code': 'USD'
            })
        
        return accounts

    def generate_accounts_csv(self, profiles: List[UserProfile]) -> List[Dict[str, Any]]:
        """Generate accounts CSV data for all users."""
        all_accounts = []
        for profile in profiles:
            user_accounts = self.generate_accounts_for_user(profile)
            all_accounts.extend(user_accounts)
        return all_accounts

    def generate_transactions_for_user(self, profile: UserProfile, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate realistic transactions for a user."""
        transactions = []
        
        # Get user's accounts
        user_accounts = [acc for acc in accounts if acc['user_id'] == profile.user_id]
        checking_accounts = [acc for acc in user_accounts if acc['subtype'] == 'checking']
        savings_accounts = [acc for acc in user_accounts if acc['subtype'] == 'savings']
        credit_accounts = [acc for acc in user_accounts if acc['subtype'] == 'credit card']
        
        # Date range for transactions
        end_date = date.today()
        start_date = end_date - timedelta(days=200)  # ~6.5 months of history
        
        # Handle edge case: insufficient data
        transaction_frequency = 1.0
        if profile.scenario == 'new_user_insufficient_data':
            start_date = end_date - timedelta(days=20)  # Only 20 days
        elif profile.scenario == 'sparse_transaction_history':
            transaction_frequency = 0.1  # Much lower frequency
        
        # Generate income transactions (payroll)
        if checking_accounts:
            checking_account = checking_accounts[0]
            income_transactions = self._generate_income_transactions(
                profile, checking_account, start_date, end_date
            )
            transactions.extend(income_transactions)
        
        # Generate subscription transactions
        subscription_transactions = self._generate_subscription_transactions(
            profile, credit_accounts + checking_accounts, start_date, end_date, transaction_frequency
        )
        transactions.extend(subscription_transactions)
        
        # Generate regular spending
        regular_transactions = self._generate_regular_transactions(
            profile, credit_accounts + checking_accounts, start_date, end_date, transaction_frequency
        )
        transactions.extend(regular_transactions)
        
        # Generate savings transactions
        if savings_accounts and checking_accounts:
            savings_transactions = self._generate_savings_transactions(
                profile, checking_accounts[0], savings_accounts[0], start_date, end_date
            )
            transactions.extend(savings_transactions)
        
        # Generate credit card payments
        if checking_accounts and credit_accounts:
            payment_transactions = self._generate_credit_payments(
                profile, checking_accounts, credit_accounts, start_date, end_date
            )
            transactions.extend(payment_transactions)
        
        # Generate bank fees (for fee_fighter persona)
        if profile.scenario == 'fee_fighter' and checking_accounts:
            fee_transactions = self._generate_bank_fees(
                profile, checking_accounts[0], start_date, end_date
            )
            transactions.extend(fee_transactions)
        
        return transactions

    def _generate_income_transactions(self, profile: UserProfile, account: Dict[str, Any], 
                                    start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Generate payroll/income transactions."""
        transactions = []
        
        # Determine income amount and frequency
        income_min, income_max = self.income_ranges[profile.income_level]
        annual_income = random.uniform(income_min, income_max)
        
        # Most people get paid bi-weekly or monthly
        if profile.scenario == 'variable_income' or profile.scenario == 'variable_income_gig_worker':
            pay_frequency = random.choice([7, 14, 21, 35, 45])  # Variable
            monthly_income = annual_income / 12
            pay_amount_base = monthly_income / 2
        else:
            pay_frequency = random.choice([14, 30])  # Bi-weekly or monthly
            if pay_frequency == 14:
                pay_amount_base = annual_income / 26  # 26 pay periods
            else:
                pay_amount_base = annual_income / 12  # 12 pay periods
        
        current_date = start_date
        while current_date <= end_date:
            # Add some variability to pay amounts
            if profile.scenario == 'variable_income' or profile.scenario == 'variable_income_gig_worker':
                pay_amount = random.uniform(pay_amount_base * 0.3, pay_amount_base * 1.8)
            else:
                pay_amount = random.uniform(pay_amount_base * 0.95, pay_amount_base * 1.05)
            
            transaction = {
                'transaction_id': f"{account['account_id']}_income_{len(transactions)}",
                'account_id': account['account_id'],
                'user_id': profile.user_id,
                'date': current_date.isoformat(),
                'amount': round(pay_amount, 2),  # Positive for income
                'merchant_name': random.choice(['Payroll Dept', 'ADP', 'Direct Deposit', 'Employer']),
                'category_primary': 'Payroll',
                'category_detailed': 'Deposit',
                'payment_channel': 'other',
                'pending': False
            }
            transactions.append(transaction)
            
            # Next pay date
            if profile.scenario == 'variable_income' or profile.scenario == 'variable_income_gig_worker':
                current_date += timedelta(days=random.randint(pay_frequency - 5, pay_frequency + 10))
            else:
                current_date += timedelta(days=pay_frequency)
        
        return transactions

    def _generate_subscription_transactions(self, profile: UserProfile, accounts: List[Dict[str, Any]], 
                                          start_date: date, end_date: date, frequency_multiplier: float) -> List[Dict[str, Any]]:
        """Generate subscription/recurring transactions."""
        transactions = []
        
        if not accounts:
            return transactions
        
        # Determine number of subscriptions based on tendency
        if profile.scenario == 'subscription_heavy':
            subscription_count = random.randint(8, 15)  # Many subscriptions
        elif profile.subscription_tendency == 'heavy':
            subscription_count = random.randint(5, 12)
        elif profile.subscription_tendency == 'moderate':
            subscription_count = random.randint(2, 6)
        else:  # light
            subscription_count = random.randint(0, 3)
        
        # Edge case adjustments
        if profile.scenario == 'high_utilization_and_subscription_heavy' or profile.scenario == 'subscription_heavy':
            subscription_count = max(6, subscription_count)
        elif profile.scenario == 'sparse_transaction_history':
            subscription_count = min(1, subscription_count)
        
        subscription_merchants = random.sample(
            self.merchant_categories['subscription'], 
            min(subscription_count, len(self.merchant_categories['subscription']))
        )
        
        for merchant in subscription_merchants:
            # Subscription amount based on service type
            if merchant in ['Netflix', 'Spotify', 'Disney+']:
                amount_range = (8.99, 15.99)
            elif merchant in ['Adobe', 'Zoom']:
                amount_range = (9.99, 39.99)
            elif merchant == 'Gym Membership':
                amount_range = (25.00, 89.99)
            else:
                amount_range = (4.99, 29.99)
            
            monthly_amount = random.uniform(*amount_range)
            
            # Generate recurring transactions
            current_date = start_date + timedelta(days=random.randint(1, 30))
            
            while current_date <= end_date:
                if random.random() < frequency_multiplier:
                    account = random.choice(accounts)
                    
                    transaction = {
                        'transaction_id': f"{account['account_id']}_sub_{merchant.replace(' ', '_')}_{current_date.strftime('%Y%m%d')}",
                        'account_id': account['account_id'],
                        'user_id': profile.user_id,
                        'date': current_date.isoformat(),
                        'amount': -round(monthly_amount, 2),  # Negative for expense
                        'merchant_name': merchant,
                        'category_primary': 'Recreation',
                        'category_detailed': 'Subscription',
                        'payment_channel': 'online',
                        'pending': False
                    }
                    transactions.append(transaction)
                
                # Next month (with slight variation)
                current_date += timedelta(days=random.randint(28, 32))
        
        return transactions

    def _generate_regular_transactions(self, profile: UserProfile, accounts: List[Dict[str, Any]], 
                                     start_date: date, end_date: date, frequency_multiplier: float) -> List[Dict[str, Any]]:
        """Generate regular spending transactions."""
        transactions = []
        
        if not accounts:
            return transactions
        
        # Base transaction frequency per day
        if profile.scenario == 'sparse_transaction_history':
            base_frequency = 0.3
        else:
            base_frequency = random.uniform(1.5, 4.0)  # 1-4 transactions per day on average
        
        current_date = start_date
        while current_date <= end_date:
            # Random number of transactions for this day
            daily_transaction_count = max(0, int(random.gauss(base_frequency * frequency_multiplier, 1)))
            
            for _ in range(daily_transaction_count):
                # Choose category and merchant
                category = random.choice(['grocery', 'gas', 'restaurant', 'shopping', 'utilities'])
                merchant = random.choice(self.merchant_categories[category])
                
                # Amount based on category and user profile  
                if category == 'grocery':
                    amount_range = (15, 150)
                elif category == 'gas':
                    amount_range = (25, 80)
                elif category == 'restaurant':
                    amount_range = (8, 45)
                elif category == 'shopping':
                    amount_range = (20, 300)
                else:  # utilities
                    amount_range = (50, 200)
                
                # Adjust for income level
                multiplier = 1.0
                if profile.income_level == 'high':
                    multiplier = 1.5
                elif profile.income_level == 'low':
                    multiplier = 0.7
                
                amount = random.uniform(amount_range[0] * multiplier, amount_range[1] * multiplier)
                account = random.choice(accounts)
                
                transaction = {
                    'transaction_id': f"{account['account_id']}_regular_{len(transactions)}",
                    'account_id': account['account_id'], 
                    'user_id': profile.user_id,
                    'date': current_date.isoformat(),
                    'amount': -round(amount, 2),  # Negative for expense
                    'merchant_name': merchant,
                    'category_primary': category.title(),
                    'category_detailed': category.title(),
                    'payment_channel': random.choice(['online', 'in store', 'other']),
                    'pending': random.choice([True, False]) if current_date >= date.today() - timedelta(days=3) else False
                }
                transactions.append(transaction)
            
            current_date += timedelta(days=1)
        
        return transactions

    def _generate_savings_transactions(self, profile: UserProfile, checking_account: Dict[str, Any], 
                                     savings_account: Dict[str, Any], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Generate savings/transfer transactions."""
        transactions = []
        
        if profile.savings_behavior == 'none':
            return transactions
        
        # Monthly savings amount based on behavior and income
        income_min, income_max = self.income_ranges[profile.income_level]
        monthly_income = (income_min + income_max) / 2 / 12
        
        if profile.savings_behavior == 'aggressive':
            savings_rate = random.uniform(0.15, 0.30)
        elif profile.savings_behavior == 'moderate':
            savings_rate = random.uniform(0.05, 0.15)
        else:  # minimal
            savings_rate = random.uniform(0.01, 0.05)
        
        # Edge case adjustments
        if profile.scenario == 'high_savings_rate':
            savings_rate = random.uniform(0.25, 0.40)
        elif profile.scenario == 'multiple_red_flags':
            return transactions  # No savings for multiple red flags
        
        monthly_savings = monthly_income * savings_rate
        
        # Generate monthly transfers
        current_date = start_date + timedelta(days=random.randint(1, 31))
        
        while current_date <= end_date:
            # Checking account outflow
            transfer_out = {
                'transaction_id': f"{checking_account['account_id']}_transfer_out_{current_date.strftime('%Y%m%d')}",
                'account_id': checking_account['account_id'],
                'user_id': profile.user_id,
                'date': current_date.isoformat(),
                'amount': -round(monthly_savings, 2),
                'merchant_name': 'Transfer to Savings',
                'category_primary': 'Transfer',
                'category_detailed': 'Deposit',
                'payment_channel': 'other',
                'pending': False
            }
            transactions.append(transfer_out)
            
            # Savings account inflow
            transfer_in = {
                'transaction_id': f"{savings_account['account_id']}_transfer_in_{current_date.strftime('%Y%m%d')}",
                'account_id': savings_account['account_id'],
                'user_id': profile.user_id,
                'date': current_date.isoformat(),
                'amount': round(monthly_savings, 2),
                'merchant_name': 'Transfer from Checking',
                'category_primary': 'Transfer',
                'category_detailed': 'Deposit',
                'payment_channel': 'other',
                'pending': False
            }
            transactions.append(transfer_in)
            
            # Next month
            current_date += timedelta(days=random.randint(28, 32))
        
        return transactions

    def _generate_credit_payments(self, profile: UserProfile, checking_accounts: List[Dict[str, Any]], 
                                credit_accounts: List[Dict[str, Any]], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Generate credit card payment transactions."""
        transactions = []
        
        if not checking_accounts or not credit_accounts:
            return transactions
        
        checking_account = checking_accounts[0]
        
        for credit_account in credit_accounts:
            current_balance = credit_account['current_balance']
            credit_limit = credit_account['credit_limit']
            
            if current_balance <= 0:
                continue  # No balance to pay
            
            # Payment behavior based on credit behavior
            if profile.credit_behavior == 'poor' or profile.scenario == 'multiple_red_flags':
                payment_ratio = random.uniform(0.02, 0.05)  # 2-5% minimum payment
            elif profile.credit_behavior == 'fair':
                payment_ratio = random.uniform(0.05, 0.15)
            else:  # good or excellent
                payment_ratio = random.uniform(0.3, 1.0)
            
            # Generate monthly payments
            current_date = start_date + timedelta(days=random.randint(15, 25))
            
            while current_date <= end_date:
                payment_amount = min(current_balance * payment_ratio, current_balance)
                
                # Reduce current balance for next month
                current_balance = max(0, current_balance - payment_amount + random.uniform(50, 300))
                
                payment = {
                    'transaction_id': f"{checking_account['account_id']}_payment_{credit_account['account_id'].split('_')[-1]}_{current_date.strftime('%Y%m%d')}",
                    'account_id': checking_account['account_id'],
                    'user_id': profile.user_id,
                    'date': current_date.isoformat(),
                    'amount': -round(payment_amount, 2),
                    'merchant_name': 'Credit Card Payment',
                    'category_primary': 'Payment',
                    'category_detailed': 'Credit Card Payment',
                    'payment_channel': 'online',
                    'pending': False
                }
                transactions.append(payment)
                
                # Next month
                current_date += timedelta(days=random.randint(28, 32))
        
        return transactions

    def _generate_bank_fees(self, profile: UserProfile, checking_account: Dict[str, Any],
                           start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Generate bank fee transactions (overdraft, ATM, maintenance fees)."""
        transactions = []
        
        # Generate 2-5 fees per month for fee_fighter persona
        fee_types = [
            ('Overdraft Fee', 35.0, 0.3),  # 30% chance per month
            ('ATM Fee', 3.0, 0.5),  # 50% chance per month
            ('Monthly Maintenance Fee', 12.0, 0.4),  # 40% chance per month
            ('Non-Sufficient Funds', 34.0, 0.2),  # 20% chance per month
        ]
        
        current_date = start_date + timedelta(days=random.randint(1, 15))
        
        while current_date <= end_date:
            for fee_name, fee_amount, probability in fee_types:
                if random.random() < probability:
                    transaction = {
                        'transaction_id': f"{checking_account['account_id']}_fee_{fee_name.replace(' ', '_')}_{current_date.strftime('%Y%m%d')}",
                        'account_id': checking_account['account_id'],
                        'user_id': profile.user_id,
                        'date': current_date.isoformat(),
                        'amount': -round(fee_amount, 2),  # Negative for fee
                        'merchant_name': 'Bank Fee',
                        'category_primary': 'Bank Fee',
                        'category_detailed': fee_name,
                        'payment_channel': 'other',
                        'pending': False
                    }
                    transactions.append(transaction)
            
            # Next month
            current_date += timedelta(days=random.randint(28, 32))
        
        return transactions

    def generate_transactions_csv(self, profiles: List[UserProfile], accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate transactions CSV data for all users."""
        all_transactions = []
        for profile in profiles:
            user_transactions = self.generate_transactions_for_user(profile, accounts)
            all_transactions.extend(user_transactions)
        return all_transactions

    def generate_liabilities_csv(self, profiles: List[UserProfile], accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate liability (credit card) data."""
        liabilities = []
        
        # Get all credit card accounts
        credit_accounts = [acc for acc in accounts if acc['type'] == 'credit']
        
        for account in credit_accounts:
            user_id = account['user_id']
            profile = next((p for p in profiles if p.user_id == user_id), None)
            
            if not profile:
                continue
            
            # APR based on credit behavior
            if profile.credit_behavior == 'excellent':
                apr = random.uniform(12.99, 18.99)
            elif profile.credit_behavior == 'good':
                apr = random.uniform(16.99, 22.99)
            elif profile.credit_behavior == 'fair':
                apr = random.uniform(19.99, 26.99)
            else:  # poor
                apr = random.uniform(24.99, 29.99)
            
            # Calculate minimum payment (typically 2-3% of balance)
            current_balance = account['current_balance']
            min_payment = max(25.0, current_balance * random.uniform(0.02, 0.03))
            
            # Last payment based on credit behavior
            if profile.credit_behavior == 'poor' or profile.scenario == 'multiple_red_flags':
                last_payment = random.uniform(min_payment * 0.8, min_payment * 1.1)
                is_overdue = random.choice([True, False])  # 50% chance
            elif profile.credit_behavior == 'fair':
                last_payment = random.uniform(min_payment, min_payment * 2.0)
                is_overdue = random.choice([True, False, False, False])  # 25% chance
            else:
                # Good/excellent: pay more than minimum
                last_payment = random.uniform(min_payment * 1.5, current_balance)
                is_overdue = False
            
            # Due date (usually 15-30 days from now)
            next_due_date = date.today() + timedelta(days=random.randint(15, 30))
            
            # Last statement balance (slightly different from current)
            last_statement = current_balance + random.uniform(-200, 200)
            last_statement = max(0, last_statement)
            
            liability = {
                'account_id': account['account_id'],
                'apr_percentage': round(apr, 2),
                'minimum_payment_amount': round(min_payment, 2),
                'last_payment_amount': round(last_payment, 2),
                'is_overdue': is_overdue,
                'next_payment_due_date': next_due_date.isoformat(),
                'last_statement_balance': round(last_statement, 2)
            }
            liabilities.append(liability)
        
        return liabilities

    def generate_all(self, user_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all synthetic data."""
        logger.info(f"Generating synthetic data for {user_count} users (seed: {self.seed})")
        
        # Generate user profiles
        profiles = self.generate_user_profiles(user_count)
        
        # Generate data in dependency order
        users_data = self.generate_users_csv(profiles)
        accounts_data = self.generate_accounts_csv(profiles)
        transactions_data = self.generate_transactions_csv(profiles, accounts_data)
        liabilities_data = self.generate_liabilities_csv(profiles, accounts_data)
        
        data = {
            'users': users_data,
            'accounts': accounts_data,
            'transactions': transactions_data,
            'liabilities': liabilities_data,
            'profiles': [profile.__dict__ for profile in profiles]
        }
        
        logger.info(f"Generated {len(users_data)} users, {len(accounts_data)} accounts, "
                   f"{len(transactions_data)} transactions, {len(liabilities_data)} liabilities")
        return data

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic financial data')
    parser.add_argument('--users', type=int, default=50, help='Number of users to generate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default='data/synthetic', help='Output directory')
    
    args = parser.parse_args()
    
    # Generate data
    generator = SyntheticDataGenerator(seed=args.seed)
    data = generator.generate_all(args.users)
    
    # Save to CSV
    generator.save_to_csv(data['users'], 'users.csv', args.output)
    generator.save_to_csv(data['accounts'], 'accounts.csv', args.output)
    generator.save_to_csv(data['transactions'], 'transactions.csv', args.output)
    generator.save_to_csv(data['liabilities'], 'liabilities.csv', args.output)
    
    print(f"✅ Generated complete dataset:")
    print(f"   👥 {len(data['users'])} users")
    print(f"   🏦 {len(data['accounts'])} accounts")
    print(f"   💳 {len(data['transactions'])} transactions")
    print(f"   📄 {len(data['liabilities'])} liabilities")
    print(f"📁 Output directory: {args.output}")
