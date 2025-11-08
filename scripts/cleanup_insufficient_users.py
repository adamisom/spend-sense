#!/usr/bin/env python3
"""
Clean up users with insufficient data quality
Either deletes them or regenerates data for them
"""
import sqlite3
import json
import argparse
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def get_insufficient_users(db_path: str = "db/spend_sense.db", min_quality: float = 0.1) -> list:
    """Get list of users with insufficient data quality."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    insufficient = []
    
    # Get all users with signals
    signals = conn.execute("""
        SELECT user_id, signals 
        FROM user_signals 
        WHERE window = '180d'
    """).fetchall()
    
    for row in signals:
        try:
            sig = json.loads(row['signals'])
            quality = sig.get('data_quality_score', 0.0)
            insufficient_flag = sig.get('insufficient_data', True)
            
            if quality < min_quality or insufficient_flag:
                insufficient.append({
                    'user_id': row['user_id'],
                    'quality': quality,
                    'insufficient': insufficient_flag
                })
        except:
            # If can't parse, consider insufficient
            insufficient.append({
                'user_id': row['user_id'],
                'quality': 0.0,
                'insufficient': True
            })
    
    # Also get users without signals at all
    all_users = conn.execute("SELECT user_id FROM users").fetchall()
    users_with_signals = {s['user_id'] for s in insufficient if 'user_id' in s}
    users_with_signals.update(row['user_id'] for row in signals)
    
    for row in all_users:
        if row['user_id'] not in users_with_signals:
            insufficient.append({
                'user_id': row['user_id'],
                'quality': 0.0,
                'insufficient': True,
                'no_signals': True
            })
    
    conn.close()
    return insufficient

def delete_users(user_ids: list, db_path: str = "db/spend_sense.db"):
    """Delete users and all their related data."""
    conn = sqlite3.connect(db_path)
    
    for user_id in user_ids:
        # Delete in order to respect foreign keys
        conn.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM recommendations WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM persona_assignments WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_signals WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM liabilities WHERE account_id IN (SELECT account_id FROM accounts WHERE user_id = ?)", (user_id,))
        conn.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        print(f"  ✅ Deleted {user_id}")
    
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Clean up users with insufficient data')
    parser.add_argument('--db-path', default='db/spend_sense.db', help='Database path')
    parser.add_argument('--min-quality', type=float, default=0.1, help='Minimum data quality score')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
    parser.add_argument('--delete', action='store_true', help='Actually delete insufficient users')
    
    args = parser.parse_args()
    
    print("🔍 Finding users with insufficient data...")
    insufficient = get_insufficient_users(args.db_path, args.min_quality)
    
    if not insufficient:
        print("✅ No users with insufficient data found!")
        return
    
    print(f"\n📊 Found {len(insufficient)} users with insufficient data:")
    for user in insufficient[:20]:  # Show first 20
        no_sig = " (no signals)" if user.get('no_signals') else ""
        print(f"  - {user['user_id']}: quality={user['quality']:.2f}, insufficient={user['insufficient']}{no_sig}")
    if len(insufficient) > 20:
        print(f"  ... and {len(insufficient) - 20} more")
    
    if args.dry_run:
        print(f"\n🔍 DRY RUN: Would delete {len(insufficient)} users")
        print("   Run with --delete to actually delete them")
    elif args.delete:
        print(f"\n🗑️  Deleting {len(insufficient)} users...")
        user_ids = [u['user_id'] for u in insufficient]
        delete_users(user_ids, args.db_path)
        print(f"\n✅ Deleted {len(insufficient)} users with insufficient data")
    else:
        print(f"\n💡 To delete these users, run:")
        print(f"   python scripts/cleanup_insufficient_users.py --delete")
        print(f"\n💡 Or to see what would be deleted:")
        print(f"   python scripts/cleanup_insufficient_users.py --dry-run")

if __name__ == "__main__":
    main()

