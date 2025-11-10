# Quick Smoke Test Guide

## 🚀 5-Minute Smoke Test

### Prerequisites
```bash
# Start Docker
colima start

# Start environment
make up && make shell
```

### Test 1: Database & Data Loading (1 min)
```bash
# Check database exists
ls -lh db/spend_sense.db

# Check data exists
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('db/spend_sense.db')
users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
txns = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f"Users: {users}, Transactions: {txns}")
conn.close()
EOF

# Expected: Users > 0, Transactions > 0
```

### Test 2: Signal Computation (2 min)
```bash
# Compute signals for first 5 users (quick test)
python scripts/compute_signals.py --limit 5

# Expected: "✅ Signal computation complete!" with success count

# Verify signals were saved
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('db/spend_sense.db')
signals = conn.execute("SELECT COUNT(*) FROM user_signals").fetchone()[0]
print(f"User signals: {signals}")
conn.close()
EOF

# Expected: signals >= 5
```

### Test 3: Dashboard Launch (1 min)
```bash
# Start dashboard (in background or new terminal)
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# Open browser: http://localhost:8501
# Expected: Dashboard loads without errors
```

### Test 4: Dashboard Functionality (1 min)
**In browser:**
1. ✅ System Overview shows user count > 0
2. ✅ "🔄 Refresh Data" and "🔧 Compute Signals" buttons visible on System Overview
3. ✅ User Analytics page loads
4. ✅ Data Quality page shows metrics
5. ✅ Recommendation Engine page loads (may take a few seconds)
6. ✅ No red error messages

### Test 5: Signal Computation from Dashboard (1 min)
**In browser:**
1. Navigate to "System Overview" page
2. Click "🔧 Compute Signals" button
3. Wait for spinner and info message (may take 1-2 minutes)
4. ✅ See success message: "✅ Signal computation complete for X users!"
5. ✅ Page auto-refreshes after 3 seconds
6. ✅ Persona data should appear (colored icons in User View instead of gray)
7. ✅ Data quality scores should be > 0

## ✅ Success Criteria

- [ ] Database has users and transactions
- [ ] Signal computation script runs without errors
- [ ] Dashboard loads without Streamlit errors
- [ ] All pages render without crashes
- [ ] Signal computation button works (on System Overview page)
- [ ] Persona data appears after computation
- [ ] Data quality scores are > 0 after computation
- [ ] Recommendations show standardized disclaimer: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
- [ ] Decision traces visible in Recommendation Engine page
- [ ] Consent management works (users without consent can't see recommendations)

## 🐛 Common Issues & Quick Fixes

**Issue: "No persona data available"**
- Fix: Navigate to System Overview page, click "🔧 Compute Signals" button, or run `python scripts/compute_signals.py`

**Issue: "Data quality is 0.0"**
- Fix: Run signal computation - signals need to be computed first

**Issue: "StreamlitAPIException: set_page_config()"**
- Fix: Already fixed - should not occur

**Issue: "Database locked"**
- Fix: Close other connections, wait a moment, retry

**Issue: "No user data found"**
- Fix: Run `python -m src.ingest.data_generator --users 50` then `python scripts/load_data.py`

## 📊 Expected Results After Full Setup

After running full signal computation:
- **Signal Coverage**: Should be 100% (all users have signals)
- **Avg Data Quality**: Should be > 0.5 (most users)
- **Persona Distribution**: Should show multiple personas
- **Fraud Analysis**: Should show fraud metrics (if fraud data exists)
- **User Analytics**: Should show charts and data

## ⚡ Quick Verification Commands

```bash
# Check everything at once
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('db/spend_sense.db')
print("=== Database Status ===")
print(f"Users: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
print(f"Transactions: {conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]}")
print(f"User Signals: {conn.execute('SELECT COUNT(*) FROM user_signals').fetchone()[0]}")
print(f"Recommendations: {conn.execute('SELECT COUNT(*) FROM recommendations').fetchone()[0]}")
conn.close()
EOF
```

