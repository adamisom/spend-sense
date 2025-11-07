# Testing Guide: Phases 1.1-1.3 Foundation

## 🎯 Purpose

This guide provides step-by-step instructions to validate that Phases 1.1 (Project Foundation), 1.2 (Database Foundation), and 1.3 (Synthetic Data Generation) are complete and working correctly before proceeding to Phase 1.4 (Data Loading).

---

## 📋 Pre-Test Checklist

Before running tests, ensure:

- [ ] Docker daemon is running (`colima start` or Docker Desktop)
- [ ] Project is initialized (`make init` if first time)
- [ ] Development container is running (`make up`)

---

## 🧪 Test Sequence

### Step 1: Validate Project Structure (Phase 1.1)

**What it tests**: Directory structure, configuration files, Docker setup

**Command**:

```bash
# Option A: Run in Docker container (recommended)
make shell
python scripts/validate_implementation.py
exit

# Option B: Run locally (if dependencies installed)
python3 scripts/validate_implementation.py
```

**Expected Output**:

```
🚀 Starting SpendSense Implementation Validation
==================================================
🏗️ Testing project structure...
✅ Project structure validation passed

📊 Testing signal schema definition...
✅ Signal schema definition validation passed

🗄️ Testing database schema...
✅ Database schema is valid SQL
✅ Database schema validation passed

🏭 Testing data generator logic...
✅ Data generator structure validation passed

📚 Testing content catalog...
✅ Content catalog validation passed (16 items)

🐳 Testing Docker configuration...
✅ Docker configuration validation passed

🔍 Testing import structure...
✅ Import structure validation passed

==================================================
🎯 Validation Results: 7 passed, 0 failed
🎉 All validation tests passed! Implementation is rock-solid.
✅ Ready for Docker deployment and external dependency testing.
```

**✅ Pass Criteria**: All 7 tests must pass

---

### Step 2: Test Signal Schema (Phase 1.2.1)

**What it tests**: UserSignals model, validation, JSON serialization

**Command**:

```bash
make shell
python -c "
from src.features.schema import UserSignals, validate_signal_completeness
from datetime import datetime

# Test valid signals
signals = UserSignals(
    credit_utilization_max=0.65,
    has_interest_charges=True,
    subscription_count=3,
    monthly_subscription_spend=89.99
)
print('✅ Valid signals created:', signals.credit_utilization_max)

# Test validation
issues = validate_signal_completeness(signals)
print('✅ Validation issues:', len(issues))

# Test JSON serialization
json_str = signals.model_dump_json()
print('✅ JSON serialization works:', len(json_str), 'chars')
print('✅ Signal schema test passed')
"
exit
```

**Expected Output**:

```
✅ Valid signals created: 0.65
✅ Validation issues: 0
✅ JSON serialization works: 200+ chars
✅ Signal schema test passed
```

**✅ Pass Criteria**: No errors, JSON serialization works

---

### Step 3: Test Database Schema & Connection (Phase 1.2.2-1.2.3)

**What it tests**: Database initialization, transactions, signal storage/retrieval

**Command**:

```bash
make shell
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals, get_user_signals
import tempfile
import os

# Test with temporary database
test_db = '/tmp/test_connection.db'

try:
    # Test initialization
    initialize_db(db_path=test_db)
    print('✅ Database initialization successful')
    
    # Test transaction
    with database_transaction(test_db) as conn:
        conn.execute('INSERT INTO users (user_id) VALUES (?)', ('test_user',))
    print('✅ Transaction successful')
    
    # Test signal storage
    test_signals = {'credit_utilization_max': 0.65, 'subscription_count': 3}
    save_user_signals('test_user', '180d', test_signals, test_db)
    print('✅ Signal storage successful')
    
    # Test signal retrieval
    retrieved = get_user_signals('test_user', '180d', test_db)
    assert retrieved['credit_utilization_max'] == 0.65
    print('✅ Signal retrieval successful')
    print('✅ Database connection test passed')
    
finally:
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
"
exit
```

**Expected Output**:

```
✅ Database initialization successful
✅ Transaction successful
✅ Signal storage successful
✅ Signal retrieval successful
✅ Database connection test passed
```

**✅ Pass Criteria**: All operations succeed without errors

---

### Step 4: Test Synthetic Data Generation (Phase 1.3.1-1.3.4)

**What it tests**: User profiles, account generation, transaction generation, liability generation, CSV output

**Command**:

```bash
make shell
python -m src.ingest.data_generator --users 5 --output /tmp/test_data

# Verify output
ls -la /tmp/test_data/
head -5 /tmp/test_data/users.csv
head -5 /tmp/test_data/accounts.csv
head -5 /tmp/test_data/transactions.csv
head -5 /tmp/test_data/liabilities.csv

# Check data volumes
wc -l /tmp/test_data/*.csv

# Clean up
rm -rf /tmp/test_data
exit
```

**Expected Output**:

```
✅ Generated complete dataset:
   👥 5 users
   🏦 10+ accounts
   💳 100+ transactions
   📄 5+ liabilities
📁 Output directory: /tmp/test_data

# Files should exist:
users.csv
accounts.csv
transactions.csv
liabilities.csv

# CSV should have proper headers and data
```

**✅ Pass Criteria**:

- All 4 CSV files created
- Users CSV has 5+ rows
- Accounts CSV has 10+ rows (2+ accounts per user)
- Transactions CSV has 100+ rows (realistic transaction history)
- Liabilities CSV has records matching credit card accounts
- Proper CSV structure with headers

---

### Step 5: Test Data Loading Pipeline (Phase 1.4)

**What it tests**: Loading CSV files into database, data integrity validation

**Command**:

```bash
make shell
# First generate test data
python -m src.ingest.data_generator --users 10 --output /tmp/test_data

# Load data into database
python scripts/load_data.py --data-dir /tmp/test_data --db-path /tmp/test.db --validate

# Verify database contents
sqlite3 /tmp/test.db "SELECT COUNT(*) FROM users;"
sqlite3 /tmp/test.db "SELECT COUNT(*) FROM accounts;"
sqlite3 /tmp/test.db "SELECT COUNT(*) FROM transactions;"
sqlite3 /tmp/test.db "SELECT COUNT(*) FROM liabilities;"

# Clean up
rm -rf /tmp/test_data /tmp/test.db
exit
```

**Expected Output**:

```
✅ Data Loading Summary:
   users: 10 records
   accounts: 20+ records
   transactions: 200+ records
   liabilities: 5+ records

🔍 Validating data integrity...
✅ Data integrity validated: 10 users loaded
✅ All data integrity checks passed
```

**✅ Pass Criteria**:

- All 4 tables loaded successfully
- Record counts match CSV files
- Data integrity validation passes
- No orphaned records or foreign key violations

---

### Step 6: Comprehensive Phase 1 Test (All Components)

**What it tests**: Complete integration of all Phase 1.1-1.4 components

**Command**:

```bash
make shell
python scripts/test_phase1.py
exit
```

**Expected Output**:

```
🚀 Starting Phase 1 Validation Tests

🧪 Testing UserSignals schema...
✅ Signal schema validation passed

🗄️ Testing database schema...
✅ Database schema validation passed

🏭 Testing synthetic data generation...
✅ Synthetic data generation validation passed

🎉 All Phase 1 validation tests passed!
Ready for Phase 2: Signal Detection
```

**✅ Pass Criteria**: All 3 tests pass

---

## 🐳 Alternative: Test in Docker (Recommended)

If you prefer to test everything in one go using Docker:

```bash
# Start environment
make up

# Run all validation tests
make shell
python scripts/validate_implementation.py
python scripts/test_phase1.py

# Test data generation
python -m src.ingest.data_generator --users 5 --output data/test
ls -la data/test/

# Clean up test data
rm -rf data/test/
exit
```

---

## ✅ Success Criteria Summary

Before moving to Phase 2, ensure:

1. **Project Structure** ✅
   - All directories exist
   - All required files present
   - Docker configuration valid

2. **Signal Schema** ✅
   - UserSignals model works
   - Validation function works
   - JSON serialization works

3. **Database Foundation** ✅
   - Schema SQL is valid
   - Database initialization works
   - Transactions work
   - Signal storage/retrieval works

4. **Data Generation** ✅
   - User profiles generate correctly
   - Accounts generate correctly
   - Transactions generate correctly (income, subscriptions, regular spending, savings, payments)
   - Liabilities generate correctly (APR, payments, overdue status)
   - All 4 CSV files output correctly

5. **Data Loading** ✅
   - CSV files load into database correctly
   - All 4 tables populated (users, accounts, transactions, liabilities)
   - Data integrity validation passes
   - No orphaned records or foreign key violations

6. **Integration** ✅
   - All components work together
   - No import errors
   - No runtime errors

---

## 🚨 Troubleshooting

### Issue: "Module not found" errors

**Solution**: Ensure you're running in Docker container (`make shell`) or have activated virtual environment

### Issue: "Database locked" errors

**Solution**: Close any other database connections, restart container (`make down && make up`)

### Issue: "CSV files not generated"

**Solution**: Check output directory permissions, ensure `data/synthetic` directory exists

### Issue: Validation script fails

**Solution**: Check that all files from Phase 1.1-1.2 exist, review error messages for specific missing components

---

## 🎯 Next Steps After Testing

Once all tests pass:

1. ✅ **Phase 1.1-1.4 Complete** - Foundation, data generation, and data loading are solid
2. ➡️ **Proceed to Phase 2** - Signal detection and persona assignment
3. ➡️ **Then Phase 3** - Recommendation engine and API

See `SpendSense-Implementation-Checklist.md` for Phase 2 and Phase 3 tasks.
