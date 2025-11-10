#!/usr/bin/env python3
"""
Wipe all existing recommendations and regenerate them with decision traces.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.db.connection import database_transaction
from scripts.generate_recommendations import generate_for_all_users
from loguru import logger


def wipe_all_recommendations(db_path: str = "db/spend_sense.db"):
    """Delete all existing recommendations from the database."""
    logger.info("🗑️  Deleting all existing recommendations...")
    
    with database_transaction(db_path) as conn:
        # Delete all recommendations
        result = conn.execute("DELETE FROM recommendations")
        count = result.rowcount
        logger.info(f"✅ Deleted {count} recommendations")
    
    return count


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Wipe and regenerate all recommendations with decision traces'
    )
    parser.add_argument(
        '--db-path', 
        default='db/spend_sense.db', 
        help='Database path'
    )
    parser.add_argument(
        '--max-recs', 
        type=int, 
        default=5, 
        help='Maximum recommendations per user'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt (use with caution)'
    )
    
    args = parser.parse_args()
    
    # Confirmation prompt
    if not args.confirm:
        print("⚠️  WARNING: This will delete ALL existing recommendations!")
        print(f"   Database: {args.db_path}")
        response = input("   Type 'yes' to continue: ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
    
    # Wipe existing recommendations
    deleted_count = wipe_all_recommendations(args.db_path)
    
    # Regenerate with decision traces
    logger.info("\n🔄 Regenerating recommendations with decision traces...")
    success_count = generate_for_all_users(args.db_path, args.max_recs)
    
    logger.info(f"\n✅ Complete!")
    logger.info(f"   Deleted: {deleted_count} old recommendations")
    logger.info(f"   Generated: {success_count} new recommendations with decision traces")


if __name__ == "__main__":
    main()

