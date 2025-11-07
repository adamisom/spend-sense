# Manual Testing Guide - Phase 1 Integration Test

## 🎯 Purpose
Quick manual integration test to verify the complete Phase 1 pipeline works end-to-end.

## 🧪 Full Integration Test

**What it tests**: Complete pipeline from data generation → CSV → database → query

**Prerequisites**:
- Docker daemon running (`colima start`)
- Container running (`make up`)

**Command**:
```bash
# Ensure container is running
make up

# Test complete pipeline end-to-end
make shell
python -m src.ingest.data_generator --users 5 --output data/test
python scripts/load_data.py --data-dir data/test --db-path db/test.db --validate
python -c "from src.db.connection import database_transaction; conn = database_transaction('db/test.db').__enter__(); print(f'Users: {conn.execute(\"SELECT COUNT(*) FROM users\").fetchone()[0]}'); print('✅ Full pipeline works')"
rm -rf data/test db/test.db
exit
```

**Expected Output**:
```
✅ Generated complete dataset:
   👥 5 users
   🏦 10+ accounts
   💳 100+ transactions
   📄 5+ liabilities
📁 Output directory: data/test

✅ Data Loading Summary:
   users: 5 records
   accounts: 10+ records
   transactions: 100+ records
   liabilities: 5+ records

🔍 Validating data integrity...
✅ Data integrity validated: 5 users loaded
✅ All data integrity checks passed

Users: 5
✅ Full pipeline works
```

**✅ Pass Criteria**: 
- All 4 CSV files generated
- All 4 tables loaded successfully
- Data integrity validation passes
- Database query returns correct user count
- No errors throughout the pipeline

---

## 📋 Quick Reference

**Start container**:
```bash
make up
```

**Access shell**:
```bash
make shell
# To exit: type 'exit' or press Ctrl+D
```

**Stop container**:
```bash
make down
```

**Restart after config changes**:
```bash
make down && make up
```

