# Phase 3 Quick Smoke Test

## 🎯 Quick Overview

Phase 3 adds two main components:

1. **Streamlit Operator Dashboard** - Visual interface for system monitoring
2. **Evaluation Metrics Engine** - Comprehensive system performance assessment

**Time**: ~5 minutes for smoke test

---

## ⚡ Quick Smoke Test (5 minutes)

### Prerequisites

```bash
# Ensure Docker is running
colima start
make up
```

### Test 1: Dashboard Startup (Basic) (1 min)

**Purpose**: Verify Streamlit can start and the app loads without import errors.

```bash
make shell

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &

# Wait a few seconds, then check
sleep 3
curl -s http://localhost:8501 | grep -i "spendsense" || echo "Dashboard accessible"

# Stop dashboard
pkill -f streamlit
exit
```

**✅ Pass**: Dashboard starts without errors, no import failures

---

### Test 2: Evaluation Metrics CLI (2 min)

```bash
make shell

# Create minimal test data
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from datetime import datetime

initialize_db()

# Create test user
user_id = 'smoke_test_user'
with database_transaction() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, consent_status, consent_date)
        VALUES (?, ?, ?)
    ''', (user_id, True, datetime.now().isoformat()))

# Create signals
signals = UserSignals(
    credit_utilization_max=0.75,
    has_interest_charges=True,
    subscription_count=3,
    data_quality_score=0.9,
    insufficient_data=False
)
save_user_signals(user_id, '180d', signals.model_dump())

# Generate recommendations
engine = RecommendationEngine()
recs = engine.generate_recommendations(user_id, signals)
save_recommendations(user_id, recs)

print(f'✅ Created test user with {len(recs)} recommendations')
"

# Run evaluation
python -m src.evaluation.metrics --window-days 7

# Cleanup: Remove test data
python -c "
from src.db.connection import database_transaction
with database_transaction() as conn:
    conn.execute('DELETE FROM recommendations WHERE user_id = ?', ('smoke_test_user',))
    conn.execute('DELETE FROM user_signals WHERE user_id = ?', ('smoke_test_user',))
    conn.execute('DELETE FROM users WHERE user_id = ?', ('smoke_test_user',))
print('✅ Cleaned up test data')
"

exit
```

**✅ Pass**: Evaluation runs and prints report with metrics

**Expected Output**:

```
# SpendSense System Evaluation Report
**Generated**: 2025-XX-XX XX:XX:XX
**Evaluation Window**: 7 days
**Users Evaluated**: 1

## 📊 Coverage Metrics
- **User Coverage**: 100.0% of users received recommendations
...
```

---

### Test 3: Dashboard Navigation & User Analytics (2 min)

**Purpose**: Verify dashboard pages render correctly, especially User Analytics with real data.

```bash
make shell

# Ensure we have some data (use existing or create minimal)
python -c "
from src.db.connection import database_transaction
with database_transaction() as conn:
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    print(f'Current users in DB: {user_count}')
    if user_count == 0:
        print('⚠️  No users found - dashboard will show empty state (this is OK for smoke test)')
"

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 3

# Manual check (open browser to http://localhost:8501):
# ✅ System Overview page shows metrics (even if zeros)
# ✅ Can navigate to "User Analytics" in sidebar dropdown
# ✅ User Analytics page loads without errors
# ✅ If data exists: charts and tables render
# ✅ If no data: shows helpful "No data" message (not blank page)

# Stop dashboard
pkill -f streamlit
exit
```

**✅ Pass**: Dashboard navigation works, User Analytics page loads (with or without data)

---

## ✅ Smoke Test Checklist

- [ ] **Test 1**: Dashboard starts without import errors
- [ ] **Test 2**: Evaluation CLI runs and generates report (test data cleaned up)
- [ ] **Test 3**: Dashboard navigation works, User Analytics page loads correctly
- [ ] No Python errors in console or browser

**If all pass**: Phase 3 smoke test successful! ✅

---

## 📚 Complete Testing Guide

For comprehensive testing with all scenarios, edge cases, and detailed validation:

👉 **See `docs/Testing-Manual.md` - Section "Phase 3: Operator Dashboard & Evaluation Framework"**

**Complete guide includes**:

- Test 1: Dashboard startup and navigation (detailed)
- Test 2: System Overview page (with test data setup)
- Test 3: User Analytics page (all sections)
- Test 4: Evaluation Metrics Engine (full scenarios)
- Test 5: Evaluation CLI with report output
- Test 6: Dashboard with real data integration

**Location**: `docs/Testing-Manual.md` lines 487-795

---

## 🐛 Quick Troubleshooting

**Dashboard won't start**:

```bash
# Check if port is in use
lsof -i :8501
# Kill if needed: kill -9 <PID>
```

**Evaluation shows 0 users**:

- Need to create users with signals and recommendations first
- See Test 2 above for setup script

**Import errors**:

```bash
# Ensure you're in container
make shell
# Check Python path
python -c "import src.ui.streamlit_app; print('✅ Imports work')"
```
