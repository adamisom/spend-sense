# Regenerate Test Users with Sufficient Data

## Problem
All test users (user_001 through user_050) have data_quality_score=0.00 and insufficient_data=True, even though they have transactions.

## Solution
Delete insufficient users and regenerate with better data diversity.

## Steps (Run in Docker)

```bash
# 1. Enter Docker shell
make shell

# 2. Delete insufficient users
python scripts/cleanup_insufficient_users.py --delete

# 3. Generate new test data (30 users with diverse profiles)
python -m src.ingest.data_generator --users 30 --output data/synthetic

# 4. Load the new data
python scripts/load_data.py --data-dir data/synthetic --db-path db/spend_sense.db

# 5. Compute signals for all users
python scripts/compute_signals.py

# 6. Verify users have good quality
python << 'EOF'
import sqlite3
import json
conn = sqlite3.connect('db/spend_sense.db')
conn.row_factory = sqlite3.Row
signals = conn.execute("SELECT user_id, signals FROM user_signals WHERE window = '180d'").fetchall()
good = [s for s in signals if json.loads(s['signals']).get('data_quality_score', 0) >= 0.1]
print(f"Users with sufficient data: {len(good)}/{len(signals)}")
conn.close()
EOF
```

## Expected Result
- All test users should have data_quality_score >= 0.1
- Users should have diverse personas (not all "Insufficient Data")
- User IDs will be user_001, user_002, etc. (regenerated)

