# Manual Testing Guide - SpendSense

## 🎯 Purpose
Quick manual integration tests to verify the complete SpendSense pipeline works end-to-end.

## Phase 1: Data Foundation Integration Test

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

---

## Phase 2: Recommendations Integration Test

**What it tests**: Complete recommendation flow from signals → persona → recommendations

**Prerequisites**:
- Docker daemon running (`colima start`)
- Container running (`make up`)
- Phase 1 data loaded (optional, for full integration)

**Command**:
```bash
# Ensure container is running
make up

# Test recommendation generation
make shell
python -c "
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine
from src.db.connection import initialize_db, save_user_signals
import json

# Initialize database
initialize_db()

# Create test user signals
signals = UserSignals(
    credit_utilization_max=0.75,
    has_interest_charges=True,
    subscription_count=5,
    monthly_subscription_spend=100.0,
    data_quality_score=0.9
)

# Save signals to database
save_user_signals('test_user', '180d', signals.model_dump())

# Generate recommendations
engine = RecommendationEngine()
recommendations = engine.generate_recommendations('test_user', signals)

print(f'✅ Generated {len(recommendations)} recommendations')
for rec in recommendations[:3]:
    print(f'  - {rec.title}: {rec.rationale}')
"

# Test persona classification
python -c "
from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona

signals = UserSignals(credit_utilization_max=0.75, data_quality_score=0.9)
match = classify_persona(signals)
print(f'✅ Persona: {match.persona_name} (confidence: {match.confidence:.2f})')
"

# Test API endpoint (if API is running)
# curl http://localhost:8000/recommendations/test_user

exit
```

**Expected Output**:
```
✅ Generated 3-5 recommendations
  - Understanding Credit Utilization: Based on your financial profile (high utilization), because your credit card utilization is above 50%, your credit utilization is 75%.
  - 5-Step Debt Paydown Strategy: Based on your financial profile (high utilization), because you're paying interest charges on credit cards.
  - Subscription Spending Tracker: Based on your financial profile (subscription-heavy), because you have 5 or more active subscriptions.

✅ Persona: High Utilization (confidence: 0.80)
```

**✅ Pass Criteria**:
- Recommendations generated successfully
- Each recommendation has a rationale
- Persona classification works correctly
- No errors during generation

---

## Unit Tests

**Run all Phase 2 unit tests**:
```bash
make shell
pytest tests/ -v
```

**Expected**: 63 tests passing

**Test Coverage**:
- Persona Classifier: 17 tests (AND/OR logic, priority, fallbacks)
- Signal Mapper: 11 tests (thresholds, multiple triggers)
- Guardrails: 9 tests (consent, safety, rate limiting)
- Recommendation Engine: 11 tests (scoring, filtering, rationales)
- Content Schema: 10 tests (validation, completeness)
- Integration: 6 tests (end-to-end flows)

