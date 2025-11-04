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
        edge_case_count = max(1, count // 10) if include_edge_cases else 0  # 10% edge cases
        
        # Generate normal profiles
        for i in range(count - edge_case_count):
            profile = UserProfile(
                user_id=f"user_{i+1:03d}",
                income_level=random.choices(['low', 'medium', 'high'], weights=[30, 50, 20])[0],
                credit_behavior=random.choices(['excellent', 'good', 'fair', 'poor'], weights=[20, 40, 25, 15])[0],
                savings_behavior=random.choices(['aggressive', 'moderate', 'minimal', 'none'], weights=[15, 35, 35, 15])[0],
                subscription_tendency=random.choices(['heavy', 'moderate', 'light'], weights=[20, 60, 20])[0],
                financial_stress=random.choice([True, False])
            )
            profiles.append(profile)
        
        # Generate edge case profiles
        if include_edge_cases:
            edge_cases = self._generate_edge_case_profiles(edge_case_count, len(profiles))
            profiles.extend(edge_cases)
        
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
            
            # Current balance (utilization)
            if profile.credit_behavior == 'poor' or profile.scenario == 'high_utilization_and_subscription_heavy':
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

    def generate_all(self, user_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all synthetic data."""
        logger.info(f"Generating synthetic data for {user_count} users (seed: {self.seed})")
        
        # Generate user profiles
        profiles = self.generate_user_profiles(user_count)
        
        # Generate data
        users_data = self.generate_users_csv(profiles)
        accounts_data = self.generate_accounts_csv(profiles)
        
        data = {
            'users': users_data,
            'accounts': accounts_data,
            'profiles': [profile.__dict__ for profile in profiles]
        }
        
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
    
    print(f"✅ Generated data for {len(data['users'])} users")
    print(f"📊 Generated {len(data['accounts'])} accounts")
    print(f"📁 Output directory: {args.output}")
