# SpendSense Product Requirements Document (PRD)

## Executive Summary

**Project**: SpendSense - Explainable Financial Education Platform  
**Goal**: Build a consent-aware system that detects behavioral patterns from transaction data, assigns personas, and delivers personalized financial education with clear guardrails.  
**Approach**: Phased MVP development prioritizing speed, explainability, and auditability.  
**Primary Priority**: Speed of development for trusted beta user testing.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Tech Stack](#tech-stack)
3. [Phase Breakdown](#phase-breakdown)
4. [Detailed Task Sequences](#detailed-task-sequences)
5. [Manual Test Checkpoints](#manual-test-checkpoints)
6. [Custom Scaffold Structure](#custom-scaffold-structure)
7. [Risks to Mitigate](#risks-to-mitigate)
8. [Success Criteria](#success-criteria)
9. [Decision Log Template](#decision-log-template)
10. [Future Work](#future-work)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SpendSense System                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Data Generator  │─────▶│  SQLite Database │◀─────│   FastAPI REST   │
│  (Synthetic)     │      │  - Users         │      │   API Server     │
└──────────────────┘      │  - Accounts      │      └──────────────────┘
                          │  - Transactions  │              │
                          │  - Consent       │              │
                          │  - Metrics       │              ▼
                          └──────────────────┘      ┌──────────────────┐
                                   │                │   Streamlit      │
                                   ▼                │   Operator View  │
                          ┌──────────────────┐      └──────────────────┘
                          │ Feature Pipeline │
                          │  - Subscriptions │
                          │  - Savings       │
                          │  - Credit Utils  │
                          │  - Income        │
                          └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Persona Engine   │
                          │  - 4 Base + TBD  │
                          │  - Priority Logic│
                          └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Recommendation   │
                          │ Engine           │
                          │  - Content Match │
                          │  - Rationale Gen │
                          └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │   Guardrails     │
                          │  - Consent Check │
                          │  - Eligibility   │
                          │  - Tone Filter   │
                          └──────────────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  Evaluation      │
                          │  Harness         │
                          │  - Metrics       │
                          │  - Reports       │
                          └──────────────────┘
```

### Key Design Principles

1. **Transparency over sophistication** - Rule-based logic with clear decision traces
2. **User control** - Explicit consent tracking, no recommendations without opt-in
3. **Education over sales** - Focus on learning, not product pushing
4. **Fast iteration** - Modular design allows independent testing of each component
5. **AI-friendly codebase** - Clear interfaces, type hints, example implementations

---

## Tech Stack

### Core Language & Runtime
- **Python 3.9+** - Maximum compatibility while maintaining modern features
- **Reason**: Best ecosystem for data processing, fast development, AI agent familiarity

### Web Framework
- **FastAPI 0.104+** - Modern, fast API framework
  - Auto-generated OpenAPI docs
  - Type validation with Pydantic
  - Async support for future scaling
- **Uvicorn** - ASGI server for FastAPI

### Data Processing
- **Pandas 2.1+** - DataFrame operations for feature engineering
  - Handles time-series windowing (30d, 180d)
  - Built-in aggregations for signal detection
  - CSV/JSON ingestion
- **NumPy 1.24+** - Numerical computations
- **Python-dateutil** - Date parsing and manipulation

### Database
- **SQLite3** (built-in) - Local storage, zero configuration
- **SQLAlchemy 2.0+** - ORM for clean data access patterns
  - Future-proof for PostgreSQL migration if needed

### UI/Operator View
- **Streamlit 1.28+** - Rapid dashboard development
  - Zero frontend code required
  - Built-in components for data visualization
  - Perfect for operator oversight interface

### Testing
- **pytest 7.4+** - Unit and integration testing
- **pytest-cov** - Code coverage reporting
- **Faker 20+** - Generate realistic synthetic data

### Utilities
- **python-dotenv** - Environment configuration
- **pydantic 2.0+** - Data validation and settings
- **loguru** - Better logging with structure

### Optional/Future
- **anthropic** - Claude API for dynamic content generation (Phase 3+)
- **polars** - Faster alternative to pandas if performance issues arise

### Development Tools
- **black** - Code formatting
- **ruff** - Fast linting
- **mypy** - Type checking

---

## Phase Breakdown

### MVP Phase 1: Data Foundation & Signal Detection
**Goal**: Generate data, detect behavioral signals, validate storage  
**Deliverable**: Working data pipeline with signal detection

**Scope**:
- Synthetic data generator (50-100 users)
- SQLite schema and ingestion pipeline
- Feature engineering for all 4 signal types
- Basic unit tests for signal detection
- Simple CLI to verify outputs

**Out of Scope**:
- Persona assignment
- Recommendations
- UI/API
- Consent tracking

**Manual Test Checkpoint**:
```bash
# Run data generator
python -m src.ingest.data_generator --users 50

# Run feature detection
python -m src.features.compute_all

# Verify outputs
python scripts/test_signals.py
```

---

### MVP Phase 2: Personas & Recommendations
**Goal**: Assign personas, generate recommendations with rationales  
**Deliverable**: End-to-end recommendation engine

**Scope**:
- Persona classification for 4 base personas
- Content catalog (5-10 items per persona, ~20 total)
- Recommendation engine with "because" rationales
- Partner offer matching with eligibility rules
- Guardrails: consent tracking, eligibility filters, tone checks
- Basic API endpoints (GET /profile, GET /recommendations)
- Evaluation metrics calculation

**Out of Scope**:
- Operator UI (Streamlit)
- Full content catalog (will have 20 items, not 50+)
- 5th custom persona

**Manual Test Checkpoint**:
```bash
# Start API server
python -m src.api.server

# Test user profile
curl http://localhost:8000/profile/user_001

# Test recommendations
curl http://localhost:8000/recommendations/user_001

# Run evaluation
python -m src.eval.run_metrics
```

---

### Phase 3: Operator View & Full Evaluation
**Goal**: Human oversight interface and comprehensive metrics  
**Deliverable**: Production-ready MVP with oversight

**Scope**:
- Streamlit operator dashboard
  - View user signals and persona
  - Review recommendations before delivery
  - Approve/override recommendations
  - Search/filter users
- Complete evaluation harness
  - Coverage, explainability, latency, fairness metrics
  - Markdown report generation
  - Per-user decision traces
- Simple user_id tracking (no authentication)
- Full test suite (10+ tests)
- Documentation: README, API docs, decision log

**Out of Scope**:
- Real OAuth/JWT authentication
- End-user UI (just API + operator view)
- LLM-generated content

**Manual Test Checkpoint**:
```bash
# Launch operator dashboard
streamlit run src/ui/operator_view.py

# Run full evaluation
python -m src.eval.generate_report

# Run test suite
pytest tests/ --cov=src --cov-report=html
```

---

### Phase 4: Future Work
**Scope**:
- 5th custom persona (define criteria, implement)
- End-user web dashboard or mobile mockup
- LLM integration for dynamic content generation
- Advanced evaluation (A/B testing framework)
- Real authentication (OAuth2, JWT)
- Performance optimization (Parquet storage, caching)
- Additional partner integrations
- Gamification features (savings challenges, badges)

---

## Detailed Task Sequences

### Phase 1 Task Breakdown

#### Task 1.1: Project Setup (30 min)
```bash
# Initialize project structure
mkdir -p spend-sense/{src,tests,data,db,docs,scripts}
cd spend-sense

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas; import fastapi; print('Setup complete')"
```

**Files Created**:
- `requirements.txt` - All pinned dependencies
- `README.md` - Setup instructions
- `.env.example` - Configuration template
- `.gitignore` - Python standard ignores

#### Task 1.2: Database Schema (1 hour)
**File**: `db/schema.sql`

**Tables**:
```sql
-- Users
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consent_status BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP
);

-- Accounts (Plaid-style)
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- checking, savings, credit card, etc.
    subtype TEXT,
    available_balance REAL,
    current_balance REAL,
    credit_limit REAL,
    iso_currency_code TEXT DEFAULT 'USD',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Transactions
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    merchant_name TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    payment_channel TEXT,
    pending BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Liabilities (Credit card details)
CREATE TABLE liabilities (
    account_id TEXT PRIMARY KEY,
    apr_percentage REAL,
    minimum_payment_amount REAL,
    last_payment_amount REAL,
    is_overdue BOOLEAN DEFAULT FALSE,
    next_payment_due_date DATE,
    last_statement_balance REAL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Computed Signals (cached)
CREATE TABLE user_signals (
    user_id TEXT NOT NULL,
    window TEXT NOT NULL,  -- '30d' or '180d'
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signals JSON NOT NULL,
    PRIMARY KEY (user_id, window),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Persona Assignments
CREATE TABLE persona_assignments (
    user_id TEXT NOT NULL,
    window TEXT NOT NULL,
    persona TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    criteria JSON NOT NULL,
    PRIMARY KEY (user_id, window),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Recommendations
CREATE TABLE recommendations (
    rec_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT NULL,
    delivered BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**Implementation**:
```python
# src/db/connection.py
import sqlite3
from pathlib import Path

def get_connection(db_path: str = "db/spend_sense.db"):
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db(schema_path: str = "db/schema.sql"):
    """Initialize database from schema file."""
    conn = get_connection()
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
```

#### Task 1.3: Synthetic Data Generator (3-4 hours)

See the PRD for the complete implementation of `SyntheticDataGenerator` class with methods for:
- `generate_users()` - Create 50-100 user records
- `generate_accounts()` - 2-4 accounts per user with diverse types
- `generate_transactions()` - Realistic spending patterns with subscriptions
- `generate_liabilities()` - Credit card details with APRs, payment info
- `generate_all()` - Orchestrate full generation
- `save_to_csv()` - Export to CSV files

**Key Features**:
- Deterministic (seed-based) for reproducibility
- Diverse financial situations (income levels, credit behaviors)
- Realistic merchant patterns (subscriptions, recurring bills)
- No real PII (uses Faker library)

#### Task 1.4: Feature Engineering - Signal Detection (4-5 hours)

Four specialized modules:

**1. Subscriptions Detection** (`src/features/subscriptions.py`):
- Detect recurring merchants (≥3 occurrences in 90 days)
- Check for monthly cadence (25-35 day gaps)
- Calculate monthly recurring spend
- Compute subscription share of total spend

**2. Savings Detection** (`src/features/savings.py`):
- Net inflow to savings-like accounts
- Savings growth rate calculation
- Emergency fund coverage (months)

**3. Credit Utilization** (`src/features/credit.py`):
- Per-card utilization calculation
- High utilization flags (30%, 50%, 80%)
- Minimum-payment-only detection
- Interest charges and overdue status

**4. Income Stability** (`src/features/income.py`):
- Payroll ACH detection via keywords
- Payment frequency and gaps
- Income variability (coefficient of variation)
- Cash-flow buffer estimation

**Orchestrator** (`src/features/compute.py`):
- `compute_user_signals()` - Run all detections for one user
- `compute_all_users()` - Batch process all users in both windows

#### Task 1.5: Unit Tests (2 hours)

**File**: `tests/test_features.py`

Test coverage:
- Subscription detection with monthly patterns
- Ignore irregular merchants
- High credit utilization flagging
- Savings growth calculation
- Income stability detection

---

### Phase 2 Task Breakdown

#### Task 2.1: Persona Definitions (1 hour)

**File**: `src/personas/definitions.py`

Define 4 base personas with:
- Clear matching criteria (rules-based)
- Primary educational focus areas
- Priority ranking (1=highest)

**Personas**:
1. **High Utilization** (Priority 1)
   - Criteria: ≥50% utilization OR interest charges OR overdue
   - Focus: Reduce utilization, payment planning, autopay

2. **Variable Income Budgeter** (Priority 2)
   - Criteria: Pay gap >45 days AND buffer <1 month
   - Focus: Percent budgets, emergency fund, smoothing

3. **Subscription-Heavy** (Priority 3)
   - Criteria: ≥3 subscriptions AND (≥$50/month OR ≥10% share)
   - Focus: Audit, cancellation, negotiation

4. **Savings Builder** (Priority 4)
   - Criteria: Growth ≥2% OR inflow ≥$200 AND utilization <30%
   - Focus: Goal setting, automation, APY optimization

#### Task 2.2: Persona Assignment (2 hours)

**File**: `src/personas/classifier.py`

`assign_persona()` function:
- Match user signals against all persona criteria
- Handle multiple matches via priority ranking
- Extract matched criteria for explainability
- Return persona assignment with rationale

#### Task 2.3: Content Catalog (2 hours)

**File**: `data/content/catalog.json`

Create 15-20 content items:
- **Articles**: 800-1500 word educational pieces
- **Checklists**: 5-10 actionable steps
- **Calculators**: Interactive financial tools
- **Partner Offers**: Product recommendations

Each item includes:
- `content_id`, `type`, `title`, `description`
- `personas` - which personas this fits
- `signals` - behavioral triggers
- `eligibility` - who can access
- `url`, `reading_time_minutes`

**Example items**:
- "Understanding Credit Utilization: The 30% Rule"
- "5-Step Debt Paydown Strategy"
- "The 10-Minute Subscription Audit"
- "High-Yield Savings Accounts: Earn 10x More"
- "ClearCard 0% Balance Transfer" (partner offer)

#### Task 2.4: Recommendation Engine (3-4 hours)

**File**: `src/recommend/engine.py`

`RecommendationEngine` class:
- `generate_recommendations()` - Main entry point
- `_score_content()` - Rank by signal relevance
- `_check_eligibility()` - Filter ineligible items
- `_generate_rationale()` - Create "because" explanations

**Output**: 3-5 education items + 1-3 partner offers per user

**Rationale examples**:
- "We noticed your credit card is at 68% utilization ($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score."
- "You have 5 recurring subscriptions totaling $89/month. A quick audit could save you $50-100/month."

#### Task 2.5: Guardrails (2-3 hours)

Three modules:

**1. Consent Management** (`src/guardrails/consent.py`):
- `grant_consent()` - Record user opt-in
- `revoke_consent()` - Delete all computed data
- `check_consent()` - Verify before recommendations

**2. Eligibility Checking** (`src/guardrails/eligibility.py`):
- Check minimum requirements (income, credit score)
- Filter products user already has
- Block harmful products (payday loans)

**3. Tone Enforcement** (`src/guardrails/tone_checker.py`):
- Prohibited phrases (shaming language)
- Positive framing checks
- Required disclaimers

#### Task 2.6: FastAPI Backend (2-3 hours)

**File**: `src/api/routes.py`

**Endpoints**:
- `GET /` - API info
- `POST /consent` - Grant/revoke consent
- `GET /profile/{user_id}` - User signals and persona
- `GET /recommendations/{user_id}` - Generate recommendations
- `POST /feedback` - Record user feedback
- `GET /operator/review` - Pending approvals queue
- `POST /operator/approve/{rec_id}` - Approve/reject

**Features**:
- Pydantic models for validation
- Database dependency injection
- Consent enforcement on all reads
- Error handling with clear messages

#### Task 2.7: Evaluation Metrics (2 hours)

**File**: `src/eval/metrics.py`

`MetricsCalculator` class:
- `calculate_coverage()` - % users with persona + ≥3 behaviors
- `calculate_explainability()` - % recommendations with rationales
- `calculate_latency()` - Time to generate recommendations
- `calculate_auditability()` - % with decision traces

`generate_report()` function:
- Markdown formatted output
- Summary table with pass/fail
- Detailed findings per metric
- Recommendations for improvements

---

### Phase 3 Task Breakdown

#### Task 3.1: Streamlit Dashboard (3-4 hours)

**File**: `src/ui/operator_view.py`

**Pages**:

1. **Overview**
   - User counts (total, consented)
   - Pending approvals
   - Persona distribution chart

2. **User Profiles**
   - User selector dropdown
   - Signals for both windows
   - Persona assignment
   - Recommendations list

3. **Recommendation Review**
   - Queue of pending recommendations
   - Approve/Reject buttons
   - View user profile link

4. **Metrics**
   - Recalculate button
   - Summary cards
   - Detailed metric displays

**Features**:
- Wide layout for data density
- Cached database connections
- Session state management
- Auto-refresh on actions

#### Task 3.2: Complete Test Suite (2-3 hours)

**File**: `tests/test_integration.py`

End-to-end tests:
- Full pipeline (generate → signals → persona → recommend)
- Consent enforcement
- Revocation deletes data
- API endpoints return expected structure
- Guardrails block ineligible recommendations

**Additional test files**:
- `tests/test_personas.py` - Persona matching logic
- `tests/test_recommend.py` - Recommendation generation
- `tests/test_guardrails.py` - Consent, eligibility, tone

**Target**: 10+ tests, >70% code coverage

#### Task 3.3: Documentation (2 hours)

**Files**:

1. **README.md**
   - Quick start guide
   - Installation steps
   - Usage examples (curl commands)
   - Project structure
   - Running tests
   - Metrics explanation

2. **docs/DECISION_LOG.md**
   - Key architectural decisions
   - Alternatives considered
   - Trade-offs and consequences
   - Future migration paths

3. **docs/API.md**
   - Endpoint documentation
   - Request/response examples
   - Error codes
   - Authentication (future)

---

## Manual Test Checkpoints

### Phase 1 Checkpoint: Data & Signals

```bash
# 1. Generate data
python -m src.ingest.data_generator --users 50

# 2. Verify CSVs created
ls -lh data/synthetic/
# Should see: users.csv, accounts.csv, transactions.csv, liabilities.csv

# 3. Load into database
python scripts/load_data.py

# 4. Compute features
python -m src.features.compute

# 5. Verify signals in database
python scripts/inspect_signals.py

# Expected output:
# - All 50 users have signals computed
# - Each signal type (subscriptions, savings, credit, income) has values
# - Both 30d and 180d windows computed

# 6. Run unit tests
pytest tests/test_features.py -v

# Expected: All tests passing
```

### Phase 2 Checkpoint: Recommendations

```bash
# 1. Start API server
uvicorn src.api.routes:app --reload &

# 2. Grant consent for test user
curl -X POST http://localhost:8000/consent \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "consented": true}'

# 3. Get user profile
curl http://localhost:8000/profile/user_001 | jq

# Expected output:
# - Persona assigned (one of 4 types)
# - Signals for both windows
# - Consent status = true

# 4. Get recommendations
curl http://localhost:8000/recommendations/user_001 | jq

# Expected output:
# - 3-5 education items
# - 1-3 partner offers
# - Each has a rationale explaining "why"
# - Rationales mention specific numbers (utilization %, amounts)

# 5. Test without consent
curl -X POST http://localhost:8000/consent \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_002", "consented": false}'

curl http://localhost:8000/recommendations/user_002

# Expected: 403 error with message about consent

# 6. Run evaluation
python -m src.eval.run_metrics

# Expected metrics:
# - Coverage: ~100%
# - Explainability: 100%
# - Latency: <5s
# - Auditability: 100%
```

### Phase 3 Checkpoint: Operator View

```bash
# 1. Launch Streamlit dashboard
streamlit run src/ui/operator_view.py

# 2. Navigate to Overview
# Verify:
# - Total users count matches generated data
# - Persona distribution chart shows all 4 personas
# - Pending approvals count > 0

# 3. Navigate to User Profiles
# Select a user
# Verify:
# - Signals displayed for both windows
# - Persona assigned with criteria
# - Recommendations shown

# 4. Navigate to Recommendation Review
# Verify:
# - List of pending recommendations
# - Can approve/reject recommendations
# - After approval, count decreases

# 5. Navigate to Metrics
# Click "Recalculate Metrics"
# Verify:
# - All metrics displayed
# - Targets shown
# - Pass/fail status indicated

# 6. Run full test suite
pytest tests/ --cov=src --cov-report=html -v

# Expected:
# - 10+ tests passing
# - Code coverage >70%

# 7. Generate final report
python -m src.eval.generate_report --output docs/evaluation_report.md

# Review markdown report
cat docs/evaluation_report.md
```

---

## Custom Scaffold Structure

Complete file tree with implementation status:

```
spend-sense/
├── README.md                           ✅ Complete setup guide
├── requirements.txt                    ✅ All dependencies pinned
├── .env.example                        ✅ Config template
├── .gitignore                          ✅ Python standard
├── main.py                             ✅ CLI runner for common tasks
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── data_generator.py          ✅ WORKING synthetic data generator
│   │   ├── validator.py                🔲 Skeleton: Validate Plaid schema
│   │   └── loader.py                   🔲 Skeleton: Load CSV/JSON to DB
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── subscriptions.py           ✅ Working detection + tests
│   │   ├── savings.py                  ✅ Working detection
│   │   ├── credit.py                   ✅ Working detection
│   │   ├── income.py                   ✅ Working detection
│   │   └── compute.py                  ✅ Orchestrator for all signals
│   │
│   ├── personas/
│   │   ├── __init__.py
│   │   ├── definitions.py             ✅ Config-driven persona rules
│   │   └── classifier.py               ✅ Assignment logic with explainability
│   │
│   ├── recommend/
│   │   ├── __init__.py
│   │   ├── engine.py                   ✅ Recommendation generation
│   │   ├── content_catalog.py          🔲 Skeleton: Load from JSON
│   │   └── rationale.py                ✅ Template system for "because"
│   │
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── consent.py                  ✅ Consent tracking
│   │   ├── eligibility.py              ✅ Product eligibility checks
│   │   └── tone_checker.py             ✅ No-shaming enforcement
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                   ✅ FastAPI with 6 endpoints
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   └── operator_view.py            ✅ Streamlit dashboard
│   │
│   ├── eval/
│   │   ├── __init__.py
│   │   ├── metrics.py                  ✅ Calculate all metrics
│   │   └── report_generator.py         ✅ Markdown report output
│   │
│   └── db/
│       ├── __init__.py
│       ├── connection.py               ✅ SQLite connection helper
│       └── schema.sql                  ✅ Complete database schema
│
├── tests/
│   ├── __init__.py
│   ├── test_data_generator.py         ✅ 3 passing tests
│   ├── test_features.py                ✅ Signal detection tests
│   ├── test_personas.py                🔲 Skeleton
│   ├── test_recommend.py               🔲 Skeleton
│   ├── test_guardrails.py              🔲 Skeleton
│   └── test_integration.py             ✅ End-to-end test
│
├── data/
│   ├── synthetic/                      📁 Generated CSVs go here
│   └── content/
│       └── catalog.json                ✅ 15 education items + offers
│
├── db/
│   ├── schema.sql                      ✅ Database schema
│   └── spend_sense.db                  🗄️ Created on first run
│
├── scripts/
│   ├── load_data.py                    ✅ CSV → Database loader
│   ├── inspect_signals.py              ✅ Debug tool for signals
│   └── test_signals.py                 ✅ Manual verification script
│
└── docs/
    ├── DECISION_LOG.md                 ✅ Template with key questions
    ├── API.md                          🔲 Skeleton: API documentation
    └── evaluation_report.md            📊 Generated after Phase 3

Legend:
✅ = Complete working implementation
🔲 = Skeleton with clear TODOs
📁 = Directory (auto-created)
🗄️ = Generated file
📊 = Generated output
```

### Scaffold Strategy

**Why custom over pre-existing**:

1. **Exact spec alignment** - Structure mirrors the project requirements
2. **Working examples** - Key modules have complete implementations
3. **AI-friendly** - Clear patterns for AI agents to extend
4. **Zero ambiguity** - Every folder has a purpose stated in docstrings
5. **Test-driven** - Failing tests guide what to implement next

**Key working files** (copy patterns from these):
- `src/features/subscriptions.py` - Signal detection template
- `src/personas/definitions.py` - Config-driven rules
- `data/content/catalog.json` - Content structure
- `tests/test_features.py` - Testing pattern

**Main entry points**:
- `main.py` - CLI commands for all operations
- `src/api/routes.py` - API endpoints
- `src/ui/operator_view.py` - Dashboard pages

---

## Risks to Mitigate

### Package Conflicts & Gotchas

#### 1. **Pandas vs. Polars**
**Risk**: Both do dataframes, may confuse AI agents  
**Mitigation**: 
- Start with **Pandas only** (more familiar, better docs)
- Document clearly if switching to Polars in Phase 3
- Never mix both in same file

**Specific versions**:
```
pandas==2.1.4
```

#### 2. **SQLAlchemy 1.x vs. 2.x**
**Risk**: Major breaking changes between versions  
**Mitigation**:
- Use **SQLAlchemy 2.0+** (modern API)
- Example patterns in scaffold use 2.0 syntax
- If issues arise, use raw `sqlite3` module (no ORM)

**Specific versions**:
```
sqlalchemy==2.0.25
```

#### 3. **FastAPI + Pydantic V2**
**Risk**: Pydantic V2 has breaking changes from V1  
**Mitigation**:
- Use **Pydantic 2.0+** consistently
- All models inherit from `pydantic.BaseModel`
- Type hints are mandatory

**Specific versions**:
```
fastapi==0.104.1
pydantic==2.5.3
```

#### 4. **Streamlit Reruns**
**Risk**: Streamlit reruns entire script on interaction, can cause state issues  
**Mitigation**:
- Use `@st.cache_resource` for database connections
- Use `st.session_state` for persistent data
- Document rerun behavior in code comments

#### 5. **Date Handling**
**Risk**: Mixing datetime, date, string dates causes bugs  
**Mitigation**:
- **Standard**: Always use `datetime.date` for dates, `datetime.datetime` for timestamps
- Use `python-dateutil` for parsing
- Store as ISO format in database

**Pattern**:
```python
from datetime import date, datetime, timedelta

# Good
transaction_date = date.today()
created_at = datetime.now()

# Bad (avoid strings)
date_str = "2024-01-15"  # Parse to date object immediately
```

#### 6. **JSON Serialization**
**Risk**: Pandas/NumPy types don't serialize to JSON directly  
**Mitigation**:
- Convert to Python native types before JSON
- Use `.to_dict()` on DataFrames
- Custom JSON encoder for edge cases

**Pattern**:
```python
# Good
result = {
    'value': float(np_array[0]),  # Convert np.float64 to float
    'count': int(df_count)         # Convert np.int64 to int
}

# Bad
result = {
    'value': np_array[0],  # May fail JSON serialization
}
```

#### 7. **Database Locking**
**Risk**: SQLite locks database file when writing  
**Mitigation**:
- Use `check_same_thread=False` in Streamlit
- Add retry logic for `sqlite3.OperationalError`
- Consider connection pooling if issues arise

**Pattern**:
```python
def get_connection():
    conn = sqlite3.connect("db/spend_sense.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
```

#### 8. **Test Isolation**
**Risk**: Tests can interfere with each other via shared database  
**Mitigation**:
- Use separate test database: `db/test_spend_sense.db`
- Fixtures should clean up after tests
- Use transactions with rollback in tests

**Pattern**:
```python
@pytest.fixture
def test_db():
    db_path = "db/test_spend_sense.db"
    # Set up
    initialize_db(db_path)
    yield db_path
    # Tear down
    os.remove(db_path)
```

#### 9. **Type Hints vs. Runtime**
**Risk**: Type hints don't enforce at runtime, can mislead  
**Mitigation**:
- Use **Pydantic** for validation at API boundaries
- Use `mypy` for static type checking (optional)
- Document when types are hints vs. validated

#### 10. **Content Catalog Loading**
**Risk**: JSON parsing errors break recommendation engine  
**Mitigation**:
- Validate JSON schema on load
- Provide clear error messages for malformed content
- Have fallback content if catalog fails to load

**Pattern**:
```python
def load_catalog(path: str) -> List[Dict]:
    try:
        with open(path) as f:
            catalog = json.load(f)
        
        # Validate required fields
        for item in catalog:
            assert 'content_id' in item
            assert 'personas' in item
        
        return catalog
    except Exception as e:
        logger.error(f"Failed to load catalog: {e}")
        return []  # Empty catalog rather than crash
```

### Dependencies Version Lock

**Complete `requirements.txt`**:
```
# Core
python-dateutil==2.8.2
faker==20.1.0

# Data processing
pandas==2.1.4
numpy==1.24.4

# Database
sqlalchemy==2.0.25

# Web framework
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.3

# UI
streamlit==1.28.2

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Utilities
python-dotenv==1.0.0
loguru==0.7.2

# Optional (future)
# anthropic==0.8.0
# polars==0.19.0
```

**Why these versions**:
- Python 3.9+ compatible
- Stable releases (not bleeding edge)
- No known security vulnerabilities as of Jan 2025
- Well-documented

### Common Pitfalls for AI Agents

1. **Don't mix raw SQL with ORM** - Pick one approach per module
2. **Always check consent before recommendations** - Enforced in API layer
3. **Rationales must cite specific numbers** - Template system helps
4. **Test with missing data** - Not all users have all signal types
5. **Handle empty dataframes gracefully** - Check `.empty` before operations

---

## Success Criteria

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Coverage | 100% | All users with consent have persona + ≥3 behaviors |
| Explainability | 100% | All recommendations have rationales citing data |
| Latency | <5 seconds | Time API endpoint `/recommendations/{user_id}` |
| Auditability | 100% | All personas have decision traces in database |
| Code Quality | 10+ tests passing | `pytest tests/ -v` |
| Documentation | Complete | README has setup + usage, decision log filled out |

**Phase-specific success**:

- **Phase 1**: Generate 50 users, compute signals, unit tests pass
- **Phase 2**: API returns recommendations with rationales, guardrails enforced
- **Phase 3**: Operator dashboard functional, evaluation report generated

---

## Decision Log Template

**File**: `docs/DECISION_LOG.md`

```markdown
# SpendSense Decision Log

## Purpose
Document key architectural and design decisions made during development.

---

## Decision 1: SQLite vs. PostgreSQL

**Date**: [Date]  
**Decision**: Use SQLite for MVP, defer PostgreSQL to production  
**Context**: 
- Need local-first development for speed
- No concurrent write requirements in MVP
- Want zero-configuration setup

**Alternatives Considered**:
- PostgreSQL: More robust, but requires Docker/install
- DuckDB: Great for analytics, but less familiar

**Consequences**:
- ✅ Faster setup (no server required)
- ✅ Single file database, easy to share
- ❌ No concurrent writes (limitation for production)
- ❌ Will need migration path to PostgreSQL

**Future Work**: Add PostgreSQL support via SQLAlchemy (same code, different connection string)

---

## Decision 2: Persona Prioritization

**Date**: [Date]  
**Decision**: Prioritize "High Utilization" persona (credit risk) over others  
**Context**:
- Users can match multiple personas
- Need clear tie-breaking rules
- Financial risk should be addressed first

**Priority Order**:
1. High Utilization (credit risk)
2. Variable Income (cash flow risk)
3. Subscription Heavy (cost optimization)
4. Savings Builder (growth opportunity)

**Rationale**: 
- Debt/credit issues can spiral quickly
- Cash flow problems are time-sensitive
- Subscriptions and savings are lower urgency

**Testing**: Created synthetic users matching multiple personas, verified priority logic

---

## Decision 3: No Authentication for MVP

**Date**: [Date]  
**Decision**: Use simple user_id tracking without passwords/JWT  
**Context**:
- Trusted beta users only
- Consent tracking requires user identity
- Real auth adds 2-4 hours development time

**Alternatives Considered**:
- Full OAuth2: Too heavy for MVP
- API keys: Better than nothing, but still overhead
- None at all: Can't track consent per user

**Consequences**:
- ✅ Faster development
- ✅ Still tracks consent per user
- ✅ Can add real auth in Phase 4
- ❌ Not production-ready
- ❌ No security for external deployment

**Future Work**: Implement OAuth2 with Auth0/Clerk before public launch

---

## Decision 4: Hardcoded Content Catalog

**Date**: [Date]  
**Decision**: Use static JSON catalog instead of LLM generation  
**Context**:
- Need predictable, auditable recommendations
- LLM adds latency and cost
- MVP has 20 items, manageable to write

**Alternatives Considered**:
- LLM generation: More flexible, but slower and less predictable
- Database-driven: Could work, but JSON is simpler for MVP
- Mix of both: Too complex for first version

**Consequences**:
- ✅ Fast, deterministic recommendations
- ✅ Easy to review and approve content
- ✅ No API costs for MVP
- ❌ Limited variety (only 20 items)
- ❌ Can't personalize tone dynamically

**Future Work**: Add LLM layer in Phase 4 for dynamic rationale generation

---

## Decision 5: [Add more decisions as you make them]

**Template**:
- Date
- Decision
- Context (why this matters)
- Alternatives considered
- Consequences (pros/cons)
- Future work if applicable
```

---

## Future Work

### Phase 4: Post-MVP Enhancements

#### 5th Custom Persona: "Fee Fighter"
**Criteria**:
- Bank fees (overdraft, ATM, monthly maintenance) ≥$20/month OR
- Excessive transaction fees detected

**Primary Focus**:
- Fee avoidance strategies
- Bank account optimization
- ATM network education
- Overdraft protection setup

**Why it matters**: Bank fees disproportionately affect lower-income users and are often avoidable with awareness.

**Implementation notes**:
- Need to detect fee transactions (category: "Bank Fees")
- Add content: "How to Avoid Bank Fees", "Free Checking Accounts Guide"
- Partner offers: Fee-free banks (fictional: FreeBank, ZeroFee Credit Union)

---

#### End-User Dashboard
**Options**:
1. React web app with dashboard view
2. Mobile-responsive web interface
3. React Native mobile app (iOS/Android)

**Features**:
- View persona and insights
- Explore recommendations
- Mark content as "helpful" or "not helpful"
- Set savings goals
- Track progress over time

---

#### LLM Integration
**Use cases**:
- **Dynamic rationales**: Generate personalized explanations on-the-fly
- **Conversational interface**: Let users ask questions about their finances
- **Content generation**: Create new education articles from templates

**Implementation**:
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def generate_rationale(signals: dict) -> str:
    prompt = f"""Generate a personalized financial insight based on these signals:
    {json.dumps(signals, indent=2)}
    
    Use empowering, supportive language. Cite specific numbers."""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text
```

---

#### Advanced Evaluation
**Additions**:
- **Fairness metrics**: Demographic parity analysis
- **A/B testing framework**: Test different recommendation strategies
- **User engagement tracking**: Click-through rates, content completion
- **Outcome tracking**: Did recommendations lead to behavior change?

---

#### Production Deployment
**Requirements**:
- Docker containerization
- PostgreSQL migration
- OAuth2 authentication (Auth0 or Clerk)
- HTTPS with SSL certificates
- Rate limiting
- Monitoring and alerting
- Backup and recovery

---

## Acknowledgments

This PRD is designed for rapid development by AI coding assistants and solo developers. The architecture prioritizes:

1. **Speed**: Get to working prototype in days, not weeks
2. **Clarity**: Clear interfaces and examples for AI agents
3. **Safety**: Guardrails prevent harmful recommendations
4. **Auditability**: Every decision is traceable

Built for Peak6's SpendSense challenge with care and attention to detail.

---

**Document Version**: 1.0  
**Last Updated**: November 3, 2025
