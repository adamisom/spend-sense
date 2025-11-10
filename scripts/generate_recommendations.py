#!/usr/bin/env python3
"""
Generate recommendations for a user or all users
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.db.connection import get_user_signals, database_transaction
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from loguru import logger


def generate_for_user(user_id: str, db_path: str = "db/spend_sense.db", max_recs: int = 5):
    """Generate recommendations for a single user."""
    # Check consent status
    with database_transaction(db_path) as conn:
        user_row = conn.execute(
            "SELECT consent_status FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        
        if not user_row:
            logger.warning(f"User {user_id} not found in database")
            return False
        
        if not user_row['consent_status']:
            logger.info(f"Skipping {user_id}: No consent (consent_status=False)")
            return False
    
    # Check if user has signals
    signals_dict = get_user_signals(user_id, '180d', db_path)
    
    if not signals_dict:
        logger.warning(f"No signals found for {user_id}. Run compute_signals.py first.")
        return False
    
    signals = UserSignals(**signals_dict)
    
    # Skip users with very low data quality (< 0.3) - insufficient data for reliable recommendations
    data_quality = signals.data_quality_score
    if data_quality < 0.3:
        logger.info(f"Skipping {user_id}: Data quality too low ({data_quality:.2f} < 0.3)")
        return False
    
    # Generate recommendations
    logger.info(f"Generating recommendations for {user_id}...")
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(
        user_id=user_id,
        signals=signals,
        max_recommendations=max_recs
    )
    
    if not recommendations:
        logger.warning(f"No recommendations generated for {user_id}")
        return False
    
    logger.info(f"Generated {len(recommendations)} recommendations")
    for rec in recommendations:
        logger.info(f"  - {rec.title}")
    
    # Save to database
    if save_recommendations(user_id, recommendations, db_path):
        logger.info(f"✅ Saved recommendations to database")
        return True
    else:
        logger.error(f"❌ Failed to save recommendations")
        return False


def generate_for_all_users(db_path: str = "db/spend_sense.db", max_recs: int = 5):
    """Generate recommendations for all users with signals."""
    with database_transaction(db_path) as conn:
        users = conn.execute("SELECT DISTINCT user_id FROM user_signals WHERE window = '180d'").fetchall()
        user_ids = [row['user_id'] for row in users]
    
    logger.info(f"Found {len(user_ids)} users with signals")
    
    success_count = 0
    for user_id in user_ids:
        if generate_for_user(user_id, db_path, max_recs):
            success_count += 1
    
    logger.info(f"\n✅ Generated recommendations for {success_count}/{len(user_ids)} users")
    return success_count


def main():
    parser = argparse.ArgumentParser(description='Generate recommendations for users')
    parser.add_argument('--user-id', help='Generate for specific user ID')
    parser.add_argument('--all', action='store_true', help='Generate for all users with signals')
    parser.add_argument('--db-path', default='db/spend_sense.db', help='Database path')
    parser.add_argument('--max-recs', type=int, default=5, help='Maximum recommendations per user')
    
    args = parser.parse_args()
    
    if args.all:
        generate_for_all_users(args.db_path, args.max_recs)
    elif args.user_id:
        generate_for_user(args.user_id, args.db_path, args.max_recs)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

