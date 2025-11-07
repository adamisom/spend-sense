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
from src.db.connection import initialize_db, save_user_signals, database_transaction
from datetime import datetime

# Initialize database
initialize_db()

# Create test user with consent (required for API endpoints)
with database_transaction() as conn:
    conn.execute("""
        INSERT OR REPLACE INTO users (user_id, consent_status, consent_date)
        VALUES (?, ?, ?)
    """, ('test_user', True, datetime.now().isoformat()))

# Create test user signals
signals = UserSignals(
    credit_utilization_max=0.75,
    has_interest_charges=True,
    subscription_count=5,
    monthly_subscription_spend=100.0,
    data_quality_score=0.9
)

# Save signals to database (datetime serialization handled automatically)
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
# First, create test user with consent and signals (required for recommendations endpoint)
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from datetime import datetime

initialize_db()

# Create user with consent
with database_transaction() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, consent_status, consent_date)
        VALUES (?, ?, ?)
    ''', ('test_user', True, datetime.now().isoformat()))

# Create and save signals
signals = UserSignals(
    credit_utilization_max=0.75,
    has_interest_charges=True,
    subscription_count=5,
    monthly_subscription_spend=100.0,
    data_quality_score=0.9
)
save_user_signals('test_user', '180d', signals.model_dump())
print('✅ User created with consent and signals')
"

# Start API server (in container)
make shell
uvicorn src.api.routes:app --host 0.0.0.0 --port 8000 &
sleep 2

# In another terminal (on host)
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/profile/test_user | jq
curl http://localhost:8000/recommendations/test_user | jq

# Stop API server with Ctrl-C 
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

---

## Phase 3: Operator Dashboard & Evaluation Framework

**What it tests**: Streamlit dashboard functionality and evaluation metrics engine

**Prerequisites**:

- Docker daemon running (`colima start`)
- Container running (`make up`)
- Phase 1 and Phase 2 data loaded (users, signals, recommendations)

### Test 1: Dashboard Startup and Navigation

```bash
make shell

# Start Streamlit dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &

# Wait for dashboard to start
sleep 5

# Check if dashboard is accessible (from host machine)
# Open browser to http://localhost:8501
# Or test with curl
curl -s http://localhost:8501 | head -20

# Stop dashboard with Ctrl+C or:
pkill -f streamlit
```

**Expected**: Dashboard loads without errors, shows System Overview page

**✅ Pass Criteria**:

- Dashboard starts without errors
- System Overview page displays
- Sidebar navigation works
- System health metrics visible

### Test 2: System Overview Page

```bash
make shell

# Ensure you have test data
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from datetime import datetime

initialize_db()

# Create test users with signals
for i in range(5):
    user_id = f'test_user_{i}'
    with database_transaction() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO users (user_id, consent_status, consent_date)
            VALUES (?, ?, ?)
        ''', (user_id, i % 2 == 0, datetime.now().isoformat()))
    
    signals = UserSignals(
        credit_utilization_max=0.5 + (i * 0.1),
        subscription_count=i,
        data_quality_score=0.7 + (i * 0.05),
        insufficient_data=False
    )
    save_user_signals(user_id, '180d', signals.model_dump())

print('✅ Test data created')
"

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5

# Manual verification:
# 1. Open http://localhost:8501 in browser
# 2. Verify System Overview page shows:
#    - Total Users metric (should show 5)
#    - Signal Coverage percentage
#    - Avg Data Quality score
#    - 24h Recommendations count
#    - Recommendation Engine status
#    - Signal Detection status
# 3. Check sidebar shows:
#    - System Health indicator
#    - Quick Stats (Users, Signal Coverage, etc.)
#    - Database path setting
#    - Refresh button

pkill -f streamlit
```

**Expected**: All metrics display correctly, system status indicators work

### Test 3: User Analytics Page

```bash
make shell

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5

# Manual verification:
# 1. Navigate to "User Analytics" in sidebar
# 2. Verify User Overview section shows:
#    - Total Users count
#    - Consent Rate percentage
#    - Users with Good Signals percentage
#    - Users with Recommendations count
# 3. Verify Persona Distribution section:
#    - Pie chart displays (if personas are assigned)
#    - Persona breakdown table shows
# 4. Verify Data Quality Analysis section:
#    - Histogram of data quality scores
#    - Quality metrics (average, median, low/high quality counts)
# 5. Verify Signal Insights section:
#    - Credit utilization distribution (if data available)
#    - Subscription count distribution
# 6. Verify User Details section:
#    - User list table displays
#    - Search functionality works
#    - Quality filter works
#    - Show count selector works

pkill -f streamlit
```

**Expected**: All analytics sections render correctly with charts and data

### Test 4: Evaluation Metrics Engine

```bash
make shell

# First, create test data with recommendations
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from datetime import datetime

initialize_db()

# Create test user with signals
user_id = 'eval_test_user'
with database_transaction() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, consent_status, consent_date)
        VALUES (?, ?, ?)
    ''', (user_id, True, datetime.now().isoformat()))

signals = UserSignals(
    credit_utilization_max=0.75,
    has_interest_charges=True,
    subscription_count=3,
    monthly_subscription_spend=50.0,
    data_quality_score=0.9,
    insufficient_data=False
)
save_user_signals(user_id, '180d', signals.model_dump())

# Generate recommendations
engine = RecommendationEngine()
recommendations = engine.generate_recommendations(user_id, signals)
save_recommendations(user_id, recommendations)

print(f'✅ Created test user with {len(recommendations)} recommendations')
"

# Run evaluation
python -m src.evaluation.metrics --window-days 7

# Expected output should show:
# - User Coverage percentage
# - Content Coverage percentage
# - Persona Distribution
# - Quality Metrics
# - Performance Metrics
# - Business Metrics
# - Guardrails Compliance
# - Success Criteria Assessment
```

**Expected Output**:

```
# SpendSense System Evaluation Report

**Generated**: 2024-XX-XX XX:XX:XX
**Evaluation Window**: 7 days
**Users Evaluated**: 1

## 📊 Coverage Metrics
- **User Coverage**: 100.0% of users received recommendations
- **Content Coverage**: XX.X% of content catalog was used

### Persona Distribution:
- High Utilization: XX.X%

## 🎯 Quality Metrics
- **Avg Recommendations per User**: X.X
- **Recommendation Diversity**: X.XX content types per user
- **Rationale Quality**: 100.0% of recommendations have rationales

## ⚡ Performance Metrics
- **95th Percentile Computation Time**: 0.0ms (estimated)
- **Error Rate**: 0.0% of users had computation errors
- **Data Quality Impact**: XX.X% correlation

## 💼 Business Metrics
- **Partner Offer Rate**: XX.X% of recommendations
- **Educational Content Rate**: XX.X% of recommendations

## 🛡️ Guardrails Compliance
- **Consent Compliance**: 100.0% (recommendations to consented users only)
- **Eligibility Compliance**: 100.0% (recommendations meeting eligibility criteria)

## 🎯 Success Criteria Assessment

### MVP Targets (✅ = Met, ❌ = Not Met):
- User Coverage ≥30%: ✅ (100.0%)
- Error Rate ≤20%: ✅ (0.0%)
- P95 Compute Time ≤500ms: ✅ (0.0ms)
- Consent Compliance 100%: ✅ (100.0%)
```

### Test 5: Evaluation CLI with Report Output

```bash
make shell

# Run evaluation and save to file
python -m src.evaluation.metrics --window-days 7 --output /tmp/evaluation_report.md

# Verify report was created
cat /tmp/evaluation_report.md | head -30

# Clean up
rm /tmp/evaluation_report.md
```

**Expected**: Report file created with comprehensive evaluation metrics

### Test 6: Dashboard with Real Data

```bash
make shell

# Generate comprehensive test dataset
python -m src.ingest.data_generator --users 20 --output data/test
python scripts/load_data.py --data-dir data/test --db-path db/spend_sense.db

# Compute signals for all users (if compute module exists)
# Otherwise, create signals manually for a few users
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
import pandas as pd

with database_transaction('db/spend_sense.db') as conn:
    users = pd.read_sql_query('SELECT user_id FROM users LIMIT 5', conn)
    
    for _, row in users.iterrows():
        user_id = row['user_id']
        signals = UserSignals(
            credit_utilization_max=0.6,
            subscription_count=2,
            data_quality_score=0.8,
            insufficient_data=False
        )
        save_user_signals(user_id, '180d', signals.model_dump(), 'db/spend_sense.db')
        
        # Generate recommendations
        engine = RecommendationEngine()
        recs = engine.generate_recommendations(user_id, signals)
        save_recommendations(user_id, recs, 'db/spend_sense.db')

print('✅ Test data with signals and recommendations created')
"

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5

# Manual verification:
# 1. System Overview should show 20 users
# 2. User Analytics should show populated charts
# 3. Persona distribution should display
# 4. All metrics should reflect the test data

pkill -f streamlit
```

**Expected**: Dashboard displays real data correctly across all pages

**✅ Pass Criteria**:

- Dashboard starts and navigates correctly
- System Overview displays accurate metrics
- User Analytics page renders all sections
- Charts and visualizations display correctly
- Evaluation engine generates comprehensive reports
- CLI evaluation tool works with file output
- No errors throughout testing

---

## Unit Tests

**Run all Phase 3 unit tests** (when available):

```bash
make shell
pytest tests/ -v -k "test_evaluation or test_dashboard"
```

**Expected**: All Phase 3 tests passing

**Test Coverage** (Phase 3):

- Evaluation Metrics: Coverage, quality, performance, business, guardrails metrics
- Dashboard Components: System health, user analytics, data visualization
- Report Generation: Evaluation report formatting and CLI interface
