# Manual Testing Guide - SpendSense

## 🎯 Purpose

Quick manual integration tests to verify the complete SpendSense pipeline works end-to-end.

---

## ⚡ Quick Smoke Test (5 minutes)

**What it tests**: Core system functionality in under 5 minutes  
**When to use**: After setup, before detailed testing, or when verifying a quick fix

**Prerequisites**:

- Docker daemon running (`colima start`)
- Container running (`make up`)

### Quick Test Steps

```bash
# 1. Start container
make up

# 2. Generate minimal test data
make shell
python -m src.ingest.data_generator --users 5 --output /tmp/smoke_test
python scripts/load_data.py --data-dir /tmp/smoke_test --db-path db/spend_sense.db

# 3. Create test user with signals and recommendations
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from datetime import datetime

initialize_db()

# Create user with consent
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

print(f'✅ Smoke test data created: {len(recs)} recommendations')
"

# 4. Quick API test
uvicorn src.api.routes:app --host 0.0.0.0 --port 8000 &
sleep 3
curl -s http://localhost:8000/health | grep -q "healthy" && echo "✅ API health check passed" || echo "❌ API health check failed"
curl -s http://localhost:8000/profile/smoke_test_user | grep -q "persona" && echo "✅ Profile endpoint works" || echo "❌ Profile endpoint failed"
pkill -f uvicorn

# 5. Quick dashboard test
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5
curl -s http://localhost:8501 | grep -q "SpendSense" && echo "✅ Dashboard loads" || echo "❌ Dashboard failed"
pkill -f streamlit

# 6. Quick test suite
pytest tests/test_features.py tests/test_personas.py -v --tb=short | tail -5

# Cleanup
rm -rf /tmp/smoke_test
exit
```

**✅ Pass Criteria** (all must pass):

- ✅ Data generation completes without errors
- ✅ Data loads into database successfully
- ✅ Recommendations generated (at least 1)
- ✅ API health endpoint returns "healthy"
- ✅ API profile endpoint returns valid JSON with persona
- ✅ Dashboard starts and loads homepage
- ✅ Core unit tests pass (features, personas)

**⏱️ Expected Time**: 3-5 minutes

**🚨 If smoke test fails**: Stop and fix issues before proceeding to detailed phase tests.

---

## Phase 1: Data Foundation Integration Test

**What it tests**: Complete pipeline from setup → validation → data generation → CSV → database → query

**Prerequisites**:

- Docker daemon running (`colima start`)
- Container running (`make up`)

### Test 1: Setup & Validate Foundation

```bash
# Install dependencies (if needed)
brew install docker colima docker-compose
xcode-select --install

# Start Docker daemon
colima start

# Initialize project (first time only)
cd /Users/adamisom/Desktop/spend-sense
make init

# Start development container (required before make shell)
make up

# Validate project structure
make shell
python scripts/validate_implementation.py
exit
```

**Expected**: All 7 validation tests pass (project structure, schema, database, data generator, content catalog, Docker config, imports)

**✅ Pass Criteria**:

- Project structure validation passes
- Database schema validation passes
- Data generator validation passes
- Content catalog validation passes
- Docker configuration validation passes
- All imports work correctly

### Test 2: Test Database Foundation

```bash
# Ensure container is running
make up

make shell
# Test signal schema
python -c "from src.features.schema import UserSignals, validate_signal_completeness; signals = UserSignals(credit_utilization_max=0.65, subscription_count=3); print('✅ Signal schema works')"

# Test database operations
python -c "from src.db.connection import initialize_db, database_transaction; initialize_db(); print('✅ Database initialization works')"
exit
```

**Expected**: No errors, schema validates, database initializes successfully

**✅ Pass Criteria**:

- Signal schema validates correctly
- Database initialization works
- No import or runtime errors

### Test 3: Test Data Generation

```bash
# Ensure container is running
make up

make shell
# Generate test data (all 4 CSV files)
python -m src.ingest.data_generator --users 10 --output /tmp/test_data

# Verify all files created
ls -la /tmp/test_data/
# Expected: users.csv, accounts.csv, transactions.csv, liabilities.csv

# Check data volumes
wc -l /tmp/test_data/*.csv
# Expected: users (10+), accounts (20+), transactions (200+), liabilities (5+)

# Clean up
rm -rf /tmp/test_data
exit
```

**Expected**: All 4 CSV files generated with realistic data volumes

**✅ Pass Criteria**:

- All 4 CSV files created (users, accounts, transactions, liabilities)
- Data volumes are realistic (10+ users, 20+ accounts, 200+ transactions, 5+ liabilities)
- No errors during generation

### Test 4: Test Data Loading Pipeline

```bash
# Ensure container is running
make up

make shell
# Generate and load test data
python -m src.ingest.data_generator --users 10 --output /tmp/test_data
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

**Expected**: All 4 tables loaded, record counts match CSV files, integrity validation passes

**✅ Pass Criteria**:

- All 4 tables loaded successfully
- Record counts match CSV file line counts
- Data integrity validation passes
- No errors during loading

### Test 5: Run Comprehensive Phase 1 Tests

```bash
# Ensure container is running
make up

make shell
python scripts/test_phase1.py
exit
```

**Expected**: All Phase 1 validation tests pass (signal schema, database, data generation)

**✅ Pass Criteria**:

- Signal schema tests pass
- Database tests pass
- Data generation tests pass
- All validation checks succeed

### Test 6: Full Integration Test

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
#    - Navigation dropdown
# 4. Check System Overview page shows:
#    - "🔄 Refresh Data" button
#    - "🔧 Compute Signals" button

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

### Test 3.5: Recommendation Engine Page

```bash
make shell

# Create test data with recommendations that have decision traces
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from datetime import datetime

initialize_db()

user_id = 'rec_engine_test_user'
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

engine = RecommendationEngine()
recs = engine.generate_recommendations(user_id, signals)
save_recommendations(user_id, recs)

print(f'✅ Created test user with {len(recs)} recommendations (with decision traces)')
"

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5

# Manual verification:
# 1. Navigate to "Recommendation Engine" in sidebar
# 2. Wait for page to load (may take a few seconds)
# 3. Verify page displays:
#    - Page explanation expander ("ℹ️ What is this page?")
#    - Filter by Status dropdown (All, Pending, Approved, Rejected)
#    - Limit number input
#    - "🔄 Refresh" button (styled, full-width, secondary type)
# 4. Verify recommendations list shows:
#    - Recommendation cards with title, user ID, type, rationale
#    - Status badges (Pending, Approved, Rejected)
#    - "🔍 View Decision Trace (Audit Trail)" expander for each recommendation
# 5. Click on a decision trace expander and verify:
#    - Full JSON trace displays
#    - Step-by-step summary shows persona classification, signal mapping, filtering, scoring
# 6. Test "🔄 Refresh" button:
#    - Click refresh button
#    - Page should reload and show latest recommendations
# 7. Test status filtering:
#    - Change filter to "Pending" - should show only pending recommendations
#    - Change filter to "Approved" - should show only approved recommendations
# 8. Test approve/reject buttons (if recommendations are pending):
#    - Click "✅ Approve" - recommendation should be marked as approved
#    - Click "❌ Reject" - recommendation should be marked as rejected

pkill -f streamlit
```

**Expected**: Recommendation Engine page displays recommendations with decision traces and refresh functionality works

**✅ Pass Criteria**:

- Recommendation Engine page loads (may take a few seconds)
- Recommendations display with all details
- Decision traces are visible and show complete audit trail
- Refresh button works to reload recommendations
- Status filtering works correctly
- Approve/Reject buttons work (if pending recommendations exist)
- No errors during page load or interactions

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

---

## Phase 4: End-User Interface & Enhanced Features

**What it tests**: End-user interface, 6 personas (including Fraud Risk), fairness metrics, decision traces, consent management, and Phase 4 enhancements

**Prerequisites**:

- Docker daemon running (`colima start`)
- Container running (`make up`)
- Phase 1, 2, and 3 data loaded (users, signals, recommendations)

### Test 1: End-User Interface (User View Page)

```bash
make shell

# Create test user with recommendations
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from datetime import datetime

initialize_db()

user_id = 'phase4_test_user'
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

engine = RecommendationEngine()
recs = engine.generate_recommendations(user_id, signals)
save_recommendations(user_id, recs)

print(f'✅ Test user created with {len(recs)} recommendations')
"

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5

# Manual verification:
# 1. Open http://localhost:8501 in browser
# 2. Navigate to "User View" in sidebar
# 3. Enter user ID: phase4_test_user
# 4. Click "🔍 Load My Profile"
# 5. Verify User View page displays:
#    - Info box: "👁️ Operator View: This page shows a mock of the end-user web application experience"
#    - Consent management section (grant/revoke consent button)
#    - Persona card with icon and description
#    - Matched criteria list
#    - "🔄 Get New Recommendations" button
#    - Recommendations section with cards
#    - Each recommendation card shows:
#      - Title and description
#      - "Why this matters" rationale
#      - Disclaimer: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
#      - Reading time and type
#      - "Learn More" button
# 6. Verify recommendations are personalized and include rationales
# 7. Test consent toggle: Revoke consent and verify recommendations are blocked
# 8. Test "Get New Recommendations" button to generate fresh recommendations

pkill -f streamlit
```

**Expected**: User View page displays personalized persona and recommendations with clear rationales

**✅ Pass Criteria**:

- User View page accessible from sidebar
- User ID input and load button work
- Consent management section displays and works
- Persona card displays correctly with icon and description
- "Get New Recommendations" button works
- Recommendations display in user-friendly cards
- Rationales are clear and personalized
- Standardized disclaimer appears on all recommendations: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
- Users without consent cannot see recommendations
- No errors during page load

### Test 2: 5th Persona (Fee Fighter)

```bash
make shell

# Test Fee Fighter persona classification
python -c "
from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona

# Test Fee Fighter persona (high fees, low utilization)
signals = UserSignals(
    credit_utilization_max=0.15,  # Low utilization
    monthly_fees_total=25.0,      # High fees
    has_interest_charges=False,
    subscription_count=1,
    data_quality_score=0.9,
    insufficient_data=False
)

match = classify_persona(signals)
print(f'✅ Persona: {match.persona_name}')
print(f'   Confidence: {match.confidence:.2f}')
print(f'   Matched criteria: {match.matched_criteria}')

# Verify it's Fee Fighter (not insufficient_data)
assert match.persona_id == 'fee_fighter', f'Expected fee_fighter, got {match.persona_id}'
print('✅ Fee Fighter persona correctly classified')
"

exit
```

**Expected**: Fee Fighter persona correctly classified for users with high fees and low utilization

**✅ Pass Criteria**:

- Fee Fighter persona exists in persona config
- Classification works for high-fee, low-utilization users
- Persona has meaningful description and criteria
- Not confused with "insufficient_data" fallback

### Test 3: Fairness Metrics in Dashboard

```bash
make shell

# Start dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
sleep 5

# Manual verification:
# 1. Open http://localhost:8501 in browser
# 2. Navigate to "Performance Metrics" page
# 3. Scroll to "⚖️ Fairness Metrics" section
# 4. Verify fairness metrics display:
#    - If no demographic data: Shows framework message with implementation notes
#    - If demographic data exists: Shows:
#      - Parity metric (coefficient of variation)
#      - Recommendation rates by demographic group
#      - Disparities detected (if any)
#      - Parity status (good/needs_review)
# 5. Verify metrics are calculated correctly

pkill -f streamlit
```

**Expected**: Fairness metrics section displays in Performance Metrics page

**✅ Pass Criteria**:

- Fairness Metrics section visible in Performance Metrics page
- Framework message displays when no demographic data available
- Parity metrics calculate correctly when demographic data exists
- Disparities are flagged appropriately (>10% difference)
- No errors during metrics calculation

### Test 4: Relevance Metrics (if implemented)

```bash
make shell

# Test relevance metrics calculation
python -c "
from src.evaluation.metrics import calculate_relevance_metrics

# This may not be implemented yet - check if it exists
try:
    metrics = calculate_relevance_metrics()
    print('✅ Relevance metrics calculated:')
    print(f'   Average relevance: {metrics.get(\"avg_relevance\", \"N/A\")}')
    print(f'   Content-persona fit: {metrics.get(\"content_persona_fit\", \"N/A\")}')
except AttributeError:
    print('ℹ️  Relevance metrics not yet implemented (Phase 4B feature)')
"

exit
```

**Expected**: Relevance metrics calculate content-persona fit scores (if implemented in Phase 4B)

**✅ Pass Criteria** (if implemented):

- Relevance metrics function exists
- Calculates average relevance score
- Calculates content-persona fit
- Metrics displayed in dashboard

### Test 5: Additional API Endpoints (Phase 4B)

```bash
make shell

# Start API server
uvicorn src.api.routes:app --host 0.0.0.0 --port 8000 &
sleep 3

# Test POST /users endpoint
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"consent_status": true}' | jq

# Test POST /consent endpoint
curl -X POST http://localhost:8000/consent \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user_4b", "consented": true}' | jq

# Test GET /recommendations/{rec_id}/view endpoint
# First get a recommendation ID
REC_ID=$(curl -s http://localhost:8000/recommendations/phase4_test_user | jq -r '.recommendations[0].rec_id // empty')
if [ -n "$REC_ID" ]; then
    curl -X POST http://localhost:8000/recommendations/$REC_ID/view | jq
    echo "✅ View endpoint works"
else
    echo "ℹ️  No recommendations found to test view endpoint"
fi

# Test POST /recommendations/{rec_id}/approve endpoint (if implemented)
if [ -n "$REC_ID" ]; then
    curl -X POST http://localhost:8000/recommendations/$REC_ID/approve \
      -H "Content-Type: application/json" \
      -d '{"approved": true, "reason": "Test approval"}' | jq || echo "ℹ️  Approve endpoint may not be implemented"
fi

pkill -f uvicorn
```

**Expected**: Additional API endpoints work correctly

**✅ Pass Criteria**:

- POST /users creates new users
- POST /consent updates consent status
- POST /recommendations/{rec_id}/view marks recommendations as viewed
- POST /recommendations/{rec_id}/approve approves recommendations (if implemented)
- All endpoints return valid JSON responses

### Test 6: End-to-End Phase 4 Flow

```bash
make shell

# Complete flow: Create user → Generate signals → Classify persona → Generate recommendations → View in User View
python -c "
from src.db.connection import initialize_db, database_transaction, save_user_signals
from src.features.schema import UserSignals
from src.personas.persona_classifier import classify_persona
from src.recommend.recommendation_engine import RecommendationEngine, save_recommendations
from datetime import datetime

initialize_db()

# Create user
user_id = 'e2e_phase4_user'
with database_transaction() as conn:
    conn.execute('''
        INSERT OR REPLACE INTO users (user_id, consent_status, consent_date)
        VALUES (?, ?, ?)
    ''', (user_id, True, datetime.now().isoformat()))

# Create signals
signals = UserSignals(
    credit_utilization_max=0.65,
    has_interest_charges=True,
    subscription_count=4,
    monthly_subscription_spend=75.0,
    monthly_fees_total=15.0,
    data_quality_score=0.85,
    insufficient_data=False
)
save_user_signals(user_id, '180d', signals.model_dump())

# Classify persona
persona = classify_persona(signals)
print(f'✅ Persona classified: {persona.persona_name}')

# Generate recommendations
engine = RecommendationEngine()
recs = engine.generate_recommendations(user_id, signals)
save_recommendations(user_id, recs)

print(f'✅ Generated {len(recs)} recommendations')
print(f'✅ End-to-end Phase 4 flow complete')
print(f'   User: {user_id}')
print(f'   Persona: {persona.persona_name}')
print(f'   Recommendations: {len(recs)}')
"

exit
```

**Expected**: Complete Phase 4 flow works end-to-end

**✅ Pass Criteria**:

- User creation works
- Signal generation works
- Persona classification works (including Fee Fighter if applicable)
- Recommendation generation works
- All data saved to database correctly
- No errors throughout flow

**✅ Pass Criteria** (Phase 4 Summary):

- End-user interface (User View) displays correctly
- 6 personas classify correctly (High Utilization, Variable Income, Subscription-Heavy, Savings Builder, Fee Fighter, Fraud Risk)
- Consent management works (users without consent blocked from recommendations)
- Decision traces visible in Recommendation Engine page
- Standardized disclaimers appear on all recommendations
- Fairness metrics display in dashboard
- Additional API endpoints work (if implemented)
- End-to-end Phase 4 flow completes successfully
- No errors throughout testing

---

## Unit Tests

**Run all Phase 4 unit tests**:

```bash
make shell
pytest tests/ -v -k "phase4 or fairness or user_view or fee_fighter"
```

**Expected**: All Phase 4 tests passing

**Test Coverage** (Phase 4):

- End-User Interface: User View page rendering, recommendation display, consent management
- Personas: All 6 personas classification (including Fraud Risk), criteria matching
- Decision Traces: Full audit trail of recommendation generation process
- Disclaimers: Standardized disclaimer text on all recommendations
- Fairness Metrics: Demographic parity calculation, disparity detection
- API Endpoints: User creation, consent management, recommendation actions
- Relevance Metrics: Content-persona fit scoring (if implemented)
- Recommendation Engine: Approval workflow, decision trace viewing, refresh functionality
