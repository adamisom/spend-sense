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

### Test 1: Persona Classification

```bash
# Ensure container is running
make up
make shell

# Test persona classification
python -c "
from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona

# Test high utilization persona
signals = UserSignals(credit_utilization_max=0.75, data_quality_score=0.9)
match = classify_persona(signals)
print(f'✅ Persona: {match.persona_name} (confidence: {match.confidence:.2f})')
print(f'   Matched criteria: {match.matched_criteria}')
"

# Test subscription heavy persona
python -c "
from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona

signals = UserSignals(subscription_count=5, monthly_subscription_spend=100.0, data_quality_score=0.9)
match = classify_persona(signals)
print(f'✅ Persona: {match.persona_name}')
"

exit
```

**Expected**: Persona correctly classified based on signals

### Test 2: Signal to Trigger Mapping

```bash
make shell

python -c "
from src.features.schema import UserSignals
from src.recommend.signal_mapper import map_signals_to_triggers, explain_triggers_for_user

signals = UserSignals(
    credit_utilization_max=0.75,
    has_interest_charges=True,
    subscription_count=5,
    monthly_subscription_spend=100.0,
    data_quality_score=0.9
)

triggers = map_signals_to_triggers(signals)
explanations = explain_triggers_for_user(triggers)

print(f'✅ Mapped {len(triggers)} triggers:')
for i, (trigger, explanation) in enumerate(zip(triggers, explanations), 1):
    print(f'   {i}. {trigger.value}: {explanation}')
"

exit
```

**Expected**: Signals correctly mapped to triggers with explanations

### Test 3: Recommendation Generation

```bash
make shell

# Create a test script file
cat > /tmp/test_recommendations.py << 'EOF'
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine
from src.db.connection import initialize_db, save_user_signals

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

print(f'\n✅ Generated {len(recommendations)} recommendations\n')
for i, rec in enumerate(recommendations[:5], 1):
    print(f'{i}. {rec.title}')
    print(f'   Type: {rec.type}')
    print(f'   Rationale: {rec.rationale}')
    print(f'   Score: {rec.priority_score:.2f}')
    print()
EOF

python /tmp/test_recommendations.py
rm /tmp/test_recommendations.py

exit
```

**Expected Output**:
```
✅ Generated 3-5 recommendations

1. Understanding Credit Utilization: The 30% Rule
   Type: article
   Rationale: Based on your financial profile (high utilization), because your credit card utilization is above 50%, your credit utilization is 75%.
   Score: 11.50

2. 5-Step Debt Paydown Strategy
   Type: checklist
   Rationale: Based on your financial profile (high utilization), because you're paying interest charges on credit cards.
   Score: 10.50
```

### Test 4: API Endpoints

```bash
# Start API server (in container)
make shell
uvicorn src.api.routes:app --host 0.0.0.0 --port 8000 &
sleep 2

# In another terminal (on host), test API
curl http://localhost:8000/health
curl http://localhost:8000/profile/test_user
curl http://localhost:8000/recommendations/test_user | jq

# Or test from within container
curl http://localhost:8000/recommendations/test_user
```

**Expected**: API returns JSON with recommendations and rationales

### Test 5: Guardrails

```bash
make shell

python -c "
from src.guardrails.guardrails import Guardrails
from src.recommend.content_schema import ContentItem, ContentType

guardrails = Guardrails()

# Test content safety
try:
    content = ContentItem(
        content_id='test',
        type=ContentType.ARTICLE,
        title='You are stupid with money',
        description='This is a test description for validation',
        personas=['high_utilization'],
        url='/test',
        reading_time_minutes=10
    )
    guardrails.validate_content_safety(content)
    print('❌ Should have caught prohibited pattern')
except Exception as e:
    print(f'✅ Guardrail caught unsafe content: {e}')
"

exit
```

**Expected**: Guardrails block unsafe content

**✅ Pass Criteria**:
- Persona classification works correctly
- Signal mapping produces correct triggers
- Recommendations generated with rationales
- API endpoints return valid JSON
- Guardrails block unsafe content
- No errors throughout the pipeline

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

