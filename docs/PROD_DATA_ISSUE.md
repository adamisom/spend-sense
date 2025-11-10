# Production Data Issue - Railway

## Problem
- **Signal Coverage: 100%** (signals exist in database)
- **Avg Data Quality: 0.00** (all signals have `data_quality_score = 0.0`)
- **All users show as gray/insufficient_data** (persona classifier assigns `insufficient_data` when quality < 0.1)

## Root Causes

### 1. Ephemeral Storage (Likely)
Railway containers are ephemeral - filesystem is wiped on each deploy unless you add a volume.

**Check:**
- Railway logs show "Initializing database..." on every deploy → data not persisting
- Run diagnostic: `bash scripts/check_persistence.sh` in Railway shell

**Fix:**
- Add Railway volume: Dashboard → Service → Settings → Volumes
- Mount path: `/app/db`
- This persists SQLite file across deploys

### 2. Silent Failures in Data Loading (Critical Bug)
If `load_data.py` or `compute_signals.py` fails silently, you'd see signals with 0.0 quality.

**Why this happens:**
- `compute_data_quality_score()` returns 0.0 when:
  - `transactions_df.empty` → score *= 0.1 (but should still be 0.1, not 0.0)
  - Multiple computation errors → score gets reduced
  - Missing critical signals → score *= 0.8

**The bug:** If transactions aren't loaded, `transactions_df` is empty, but signals are still saved with 0.0 quality instead of failing loudly.

**What to check:**
1. Railway logs for `load_data.py` - does it show "Loaded X transactions"?
2. Railway logs for `compute_signals.py` - does it show "✅ Saved signals for user_XXX (quality: X.XX)"?
3. Database contents: `SELECT COUNT(*) FROM transactions` - should be > 0

**Fix needed:**
- Make `load_data.py` fail loudly if no transactions loaded (currently returns 0 silently)
- Make `compute_signals.py` fail loudly if transactions_df is empty (currently computes signals with 0.0 quality)
- Add validation: don't save signals with quality = 0.0 unless explicitly insufficient_data
- In `railway_init.sh`: Check transaction count after loading and fail if 0

## Quick Diagnostic

Run in Railway shell:
```bash
bash scripts/check_persistence.sh
```

Or manually:
```bash
# Check if database exists and has data
python3 -c "
import sqlite3
conn = sqlite3.connect('/app/db/spend_sense.db')
print('Users:', conn.execute('SELECT COUNT(*) FROM users').fetchone()[0])
print('Transactions:', conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0])
print('Signals:', conn.execute(\"SELECT COUNT(*) FROM user_signals WHERE window = '180d'\").fetchone()[0])
conn.close()
"
```

## Next Steps

1. **Immediate:** Check Railway logs for data loading errors
2. **Short-term:** Add Railway volume for persistence
3. **Fix:** Make data loading fail loudly instead of silently creating 0.0 quality signals
4. **Long-term:** Consider Postgres (Railway managed service) instead of SQLite

