# SpendSense Product Requirements Document (PRD)
## Reconstructed from Implementation Documentation

**Version**: 1.0  
**Last Updated**: 2025-01-07  
**Status**: Reconstructed from implementation docs, architecture guide, and testing manual

---

## Executive Summary

**Project**: SpendSense - Explainable Financial Education Platform  
**Goal**: Build a consent-aware system that detects behavioral patterns from transaction data, assigns personas, and delivers personalized financial education with clear guardrails.  
**Approach**: Phased MVP development prioritizing speed, explainability, and auditability.  
**Primary Priority**: Speed of development for trusted beta user testing.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Core Design Principles](#core-design-principles)
3. [Tech Stack](#tech-stack)
4. [Phase Breakdown](#phase-breakdown)
5. [Functional Requirements](#functional-requirements)
6. [Non-Functional Requirements](#non-functional-requirements)
7. [Success Criteria](#success-criteria)
8. [Data Model](#data-model)
9. [API Specification](#api-specification)
10. [Guardrails & Safety](#guardrails--safety)
11. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

### System Overview

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
                         │  - Signals       │              ▼
                         │  - Recommendations│     ┌──────────────────┐
                         └──────────────────┘     │   Streamlit      │
                                  │                │   Operator View  │
                                  ▼                └──────────────────┘
                         ┌──────────────────┐
                         │ Signal Pipeline │
                         │ - Detection     │
                         │ - Classification│
                         │ - Recommendation│
                         └──────────────────┘
```

### Data Flow

1. **Data Ingestion**: Synthetic transaction data → CSV files → SQLite database
2. **Signal Detection**: Transaction data → Behavioral signals (credit, income, subscriptions, savings)
3. **Persona Classification**: Signals → Persona assignment (5 personas)
4. **Recommendation Generation**: Persona + Signals → Content recommendations with rationales
5. **Guardrails**: Recommendations filtered for consent, safety, compliance
6. **Delivery**: Recommendations stored in database, accessible via API and operator dashboard

---

## Core Design Principles

1. **Explainability First**: Every recommendation must have a clear "because" rationale
2. **Incremental Complexity**: Start simple, add sophistication iteratively
3. **Data Privacy by Design**: User consent and data minimization throughout
4. **Fail-Safe Operations**: Graceful degradation when components fail
5. **Audit Trail Everything**: Complete traceability of all decisions and data

### Technical Philosophy

- **Monolithic MVP**: Single deployable unit for faster iteration
- **Event-Driven Signals**: Clear separation between data ingestion and signal computation
- **Configuration-Driven Logic**: Business rules externalized for non-technical modification
- **Database-Centric**: SQLite as single source of truth with strong consistency
- **API-First UI**: All functionality exposed via REST API, consumed by Streamlit

---

## Tech Stack

### Core Technologies
- **Language**: Python 3.11
- **Database**: SQLite (MVP), PostgreSQL (production scale)
- **API Framework**: FastAPI 0.104.1
- **UI Framework**: Streamlit 1.28.2
- **Data Processing**: Pandas 2.1.4, NumPy 1.24.4
- **Validation**: Pydantic 2.5.3
- **Testing**: pytest 7.4.3

### Infrastructure
- **Containerization**: Docker with docker-compose
- **Development**: Colima (macOS Docker daemon)
- **Deployment**: Single-server monolithic deployment for MVP

### External Dependencies
- **Synthetic Data**: Faker 20.1.0
- **Logging**: loguru 0.7.2
- **Configuration**: PyYAML 6.0.1

---

## Phase Breakdown

### Phase 1: Data Foundation & Signal Detection
**Goal**: Working data pipeline with signal detection  
**Estimated Time**: 12-16 hours  
**Success Criteria**: All 50 synthetic users have computed signals, unit tests pass

**Key Deliverables**:
- Database schema (7 tables: users, accounts, transactions, liabilities, user_signals, persona_assignments, recommendations)
- Synthetic data generator (users, accounts, transactions, liabilities)
- Data loading pipeline (CSV → database with integrity validation)
- Signal detection schema (UserSignals Pydantic model)
- Content catalog (20+ financial education items)

**Signal Types Detected**:
- **Credit Signals**: `credit_utilization_max`, `has_interest_charges`, `is_overdue`, `minimum_payment_only`
- **Income Signals**: `income_pay_gap`, `cash_flow_buffer`, `income_variability`
- **Subscription Signals**: `subscription_count`, `monthly_subscription_spend`, `subscription_share`
- **Savings Signals**: `savings_growth_rate`, `monthly_savings_inflow`, `emergency_fund_months`
- **Data Quality**: `insufficient_data`, `data_quality_score`, `computation_errors`

### Phase 2: Personas & Recommendations
**Goal**: End-to-end recommendation engine with rationales  
**Estimated Time**: 18-24 hours  
**Success Criteria**: API returns recommendations with "because" rationales, guardrails enforced

**Key Deliverables**:
- Persona classification engine (5 personas with configurable criteria)
- Signal-to-trigger mapping (converts numeric signals to categorical triggers)
- Recommendation engine (7-step pipeline: persona → triggers → filtering → scoring → ranking → rationale)
- Content schema with validation (Pydantic models)
- FastAPI endpoints (`/profile/{user_id}`, `/recommendations/{user_id}`)
- Guardrails system (consent, content safety, rate limiting)

**Personas**:
1. **High Utilization** (Priority 1): Credit utilization ≥50%, interest charges, overdue payments
2. **Variable Income** (Priority 2): Income gaps >45 days, cash buffer <1 month
3. **Subscription-Heavy** (Priority 3): ≥3 subscriptions, ≥$50/month spend, ≥10% of total spend
4. **Savings Builder** (Priority 4): Positive savings growth, ≥$200/month inflow, utilization <30%
5. **Insufficient Data** (Priority 999): Fallback for low data quality

**Content Types**:
- Articles (educational content)
- Checklists (actionable steps)
- Calculators (interactive tools)
- Partner Offers (financial product recommendations)

### Phase 3: Operator View & Full Evaluation
**Goal**: Complete production-ready system with operator dashboard and evaluation metrics  
**Estimated Time**: 14-18 hours  
**Success Criteria**: Working Streamlit dashboard, comprehensive test suite, production readiness checklist

**Key Deliverables**:
- Streamlit operator dashboard (multi-page: System Overview, User Analytics, Recommendation Engine, Data Quality, Performance Metrics, System Logs)
- Evaluation metrics engine (coverage, quality, performance, business, guardrails metrics)
- Evaluation report generation (CLI tool with markdown output)
- Comprehensive test suite (63+ unit tests)

---

## Functional Requirements

### FR1: Data Ingestion
- **FR1.1**: System must generate synthetic financial data (users, accounts, transactions, liabilities)
- **FR1.2**: System must load CSV data into SQLite database with integrity validation
- **FR1.3**: System must preserve all raw transaction data for reprocessing and auditing

### FR2: Signal Detection
- **FR2.1**: System must compute behavioral signals from transaction data
- **FR2.2**: System must support multiple time windows (30d, 180d)
- **FR2.3**: System must calculate data quality scores (0.0-1.0)
- **FR2.4**: System must flag insufficient data when thresholds not met
- **FR2.5**: System must store signals as JSON for schema flexibility

### FR3: Persona Classification
- **FR3.1**: System must classify users into personas based on signal criteria
- **FR3.2**: System must support AND/OR combinators for multi-criteria matching
- **FR3.3**: System must use priority-based tie-breaking for multiple matches
- **FR3.4**: System must fall back to "insufficient_data" persona when no match or low data quality
- **FR3.5**: System must store persona assignments with matched criteria for explainability

### FR4: Recommendation Generation
- **FR4.1**: System must generate 3-5 personalized recommendations per user
- **FR4.2**: System must provide a "because" rationale for each recommendation
- **FR4.3**: System must filter content by persona, signal triggers, and eligibility
- **FR4.4**: System must exclude recently viewed content (30-day default window)
- **FR4.5**: System must score and rank recommendations by relevance
- **FR4.6**: System must persist recommendations to database

**Recommendation Pipeline**:
1. Persona Classification
2. Signal to Trigger Mapping
3. Recent Content Deduplication
4. Content Filtering (persona + triggers)
5. Eligibility Checking
6. Scoring & Ranking
7. Rationale Generation

**Scoring Formula**:
```
final_score = (
    persona_match_score * 0.4 +
    signal_match_score * 0.3 + 
    content_priority_score * 0.2 +
    freshness_score * 0.1
)
```

### FR5: Guardrails & Safety
- **FR5.1**: System must enforce 100% consent compliance (no recommendations to non-consented users)
- **FR5.2**: System must detect and block prohibited content patterns (financial shaming language)
- **FR5.3**: System must enforce positive framing (rewrite negative language)
- **FR5.4**: System must inject required disclaimers by content type
- **FR5.5**: System must implement rate limiting per user
- **FR5.6**: System must log all guardrail decisions for audit

### FR6: API Endpoints
- **FR6.1**: System must provide `/health` endpoint for system status
- **FR6.2**: System must provide `/profile/{user_id}` endpoint returning persona, signals, and triggers
- **FR6.3**: System must provide `/recommendations/{user_id}` endpoint returning personalized recommendations
- **FR6.4**: System must provide `/recommendations/{rec_id}/approve` endpoint for approval workflow
- **FR6.5**: System must provide `/recommendations/{rec_id}/view` endpoint for view tracking

### FR7: Operator Dashboard
- **FR7.1**: System must provide Streamlit dashboard for operators
- **FR7.2**: Dashboard must show system overview with health metrics
- **FR7.3**: Dashboard must show user analytics (persona distribution, data quality, signal insights)
- **FR7.4**: Dashboard must show recommendation engine metrics
- **FR7.5**: Dashboard must show data quality analysis
- **FR7.6**: Dashboard must show performance metrics
- **FR7.7**: Dashboard must allow database path configuration

### FR8: Evaluation & Metrics
- **FR8.1**: System must calculate coverage metrics (user, persona, content)
- **FR8.2**: System must calculate quality metrics (diversity, rationale quality)
- **FR8.3**: System must calculate performance metrics (error rate, computation time, data quality impact)
- **FR8.4**: System must calculate business metrics (partner offer rate, educational content rate)
- **FR8.5**: System must calculate guardrails compliance metrics
- **FR8.6**: System must generate evaluation reports (markdown format)
- **FR8.7**: System must provide CLI tool for running evaluations

---

## Non-Functional Requirements

### NFR1: Performance
- **NFR1.1**: Recommendation generation must complete in <500ms (95th percentile)
- **NFR1.2**: API endpoints must respond in <200ms (95th percentile)
- **NFR1.3**: Dashboard must load in <2 seconds
- **NFR1.4**: System must support concurrent read operations (WAL mode)

### NFR2: Reliability
- **NFR2.1**: System must have error rate ≤20% (users with signals but no recommendations)
- **NFR2.2**: System must gracefully handle missing data
- **NFR2.3**: System must provide fallback personas when classification fails
- **NFR2.4**: System must retry database operations with exponential backoff

### NFR3: Scalability
- **NFR3.1**: System must support 50-100 users for beta testing
- **NFR3.2**: Database must use indexes for common queries
- **NFR3.3**: System must be designed for migration to PostgreSQL when needed

### NFR4: Security & Privacy
- **NFR4.1**: System must enforce 100% consent compliance (legal requirement)
- **NFR4.2**: System must use parameterized queries (SQL injection prevention)
- **NFR4.3**: System must log all data access for audit
- **NFR4.4**: System must support data minimization (only store necessary data)

### NFR5: Maintainability
- **NFR5.1**: Business rules must be externalized in YAML/JSON config files
- **NFR5.2**: Code must have 80%+ test coverage for critical paths
- **NFR5.3**: System must have comprehensive documentation
- **NFR5.4**: System must use type hints and Pydantic validation

### NFR6: Usability
- **NFR6.1**: Operator dashboard must be intuitive for non-technical users
- **NFR6.2**: Recommendations must have clear, understandable rationales
- **NFR6.3**: System must provide clear error messages

---

## Success Criteria

### MVP Targets

1. **User Coverage ≥30%**: At least 30% of users receive recommendations
2. **Error Rate ≤20%**: No more than 20% of users with signals fail to get recommendations
3. **P95 Compute Time ≤500ms**: 95th percentile recommendation generation time under 500ms
4. **Consent Compliance 100%**: 100% of recommendations go to consented users only (legal requirement)

### Phase Completion Criteria

**Phase 1 Complete When**:
- ✅ All 4 CSV files generate with realistic data
- ✅ Database initializes and stores data correctly
- ✅ Data loads with integrity validation passing
- ✅ Signal schema validates correctly
- ✅ Full pipeline works end-to-end

**Phase 2 Complete When**:
- ✅ Content schema validates correctly
- ✅ Signal mapper converts signals to triggers accurately
- ✅ Persona classifier matches users to personas with AND/OR logic
- ✅ Recommendation engine generates personalized recommendations
- ✅ API endpoints return recommendations with rationales
- ✅ Guardrails enforce safety and compliance
- ✅ 63 unit tests passing

**Phase 3 Complete When**:
- ✅ Streamlit dashboard displays system metrics
- ✅ User analytics page shows persona distribution and signal insights
- ✅ Evaluation engine generates comprehensive reports
- ✅ All Phase 3 tests passing (12+ tests)

---

## Data Model

### Database Schema (7 Tables)

1. **users**: `user_id` (PK), `created_at`, `consent_status`, `consent_date`
2. **accounts**: `account_id` (PK), `user_id` (FK), `type`, `subtype`, `available_balance`, `current_balance`, `credit_limit`
3. **transactions**: `transaction_id` (PK), `account_id` (FK), `user_id` (FK), `date`, `amount`, `merchant_name`, `category_primary`, `category_detailed`, `payment_channel`, `pending`
4. **liabilities**: `account_id` (PK, FK), `apr_percentage`, `minimum_payment_amount`, `last_payment_amount`, `is_overdue`, `next_payment_due_date`, `last_statement_balance`
5. **user_signals**: `user_id` (PK), `window` (PK), `computed_at`, `signals` (JSON)
6. **persona_assignments**: `user_id` (PK), `window` (PK), `persona`, `assigned_at`, `criteria` (JSON)
7. **recommendations**: `rec_id` (PK), `user_id` (FK), `content_id`, `rationale`, `created_at`, `approved`, `delivered`, `viewed_at`

### Signal Schema (UserSignals)

**Credit Signals**:
- `credit_utilization_max`: Optional[float] (0.0-1.0)
- `has_interest_charges`: bool
- `is_overdue`: bool
- `minimum_payment_only`: bool

**Income Signals**:
- `income_pay_gap`: Optional[int] (days)
- `cash_flow_buffer`: Optional[float] (months)
- `income_variability`: Optional[float] (coefficient of variation)

**Subscription Signals**:
- `subscription_count`: int (≥0)
- `monthly_subscription_spend`: float (≥0.0)
- `subscription_share`: float (0.0-1.0)

**Savings Signals**:
- `savings_growth_rate`: Optional[float] (can be negative)
- `monthly_savings_inflow`: float (≥0.0)
- `emergency_fund_months`: Optional[float] (≥0.0)

**Data Quality**:
- `insufficient_data`: bool
- `data_quality_score`: float (0.0-1.0)
- `computation_errors`: List[str]

**Metadata**:
- `computed_at`: datetime
- `window`: str ("30d" or "180d")

### Content Catalog Schema

**ContentItem Fields**:
- `content_id`: str (unique identifier)
- `type`: ContentType enum (article, checklist, calculator, partner_offer)
- `title`: str (5-200 chars)
- `description`: str (10-1000 chars)
- `personas`: List[str] (which personas this targets)
- `signal_triggers`: List[SignalTrigger] (behavioral triggers)
- `url`: str (content URL)
- `reading_time_minutes`: int (1-120)
- `difficulty_level`: str (beginner, intermediate, advanced)
- `eligibility`: EligibilityRequirements (income, credit score, account types)
- `priority_score`: float (0.0-10.0)
- `tags`: List[str]

**Content Catalog**: 20+ items covering all personas and signal triggers

---

## API Specification

### Base URL
`http://localhost:8000` (development)

### Endpoints

#### `GET /`
**Description**: Root endpoint  
**Response**: Service name, version, status

#### `GET /health`
**Description**: Health check  
**Response**: `{"status": "healthy"}`

#### `GET /profile/{user_id}`
**Description**: Get user profile with persona and signals  
**Query Parameters**:
- `window`: str (optional, default: "180d") - Time window for signals

**Response**:
```json
{
  "user_id": "user123",
  "persona": {
    "persona_id": "high_utilization",
    "persona_name": "High Utilization",
    "priority": 1,
    "confidence": 0.85,
    "matched_criteria": ["Credit utilization 50% or higher"]
  },
  "signals": { /* UserSignals object */ },
  "triggers": ["high_credit_utilization", "has_interest_charges"]
}
```

#### `GET /recommendations/{user_id}`
**Description**: Get personalized recommendations  
**Query Parameters**:
- `window`: str (optional, default: "180d")
- `max_recommendations`: int (optional, default: 5)

**Response**:
```json
{
  "user_id": "user123",
  "recommendations": [
    {
      "rec_id": "uuid",
      "content_id": "credit_utilization_guide",
      "title": "Understanding Credit Utilization: The 30% Rule",
      "description": "...",
      "url": "/content/credit-utilization-guide",
      "type": "article",
      "reading_time_minutes": 12,
      "rationale": "Based on your financial profile (high utilization), because your credit card utilization is above 50%, your credit utilization is 75%.",
      "priority_score": 11.5,
      "match_reasons": ["Matches High Utilization persona", "Matches high_credit_utilization trigger"]
    }
  ],
  "generated_at": "2025-01-07T12:00:00Z",
  "persona": "high_utilization"
}
```

#### `POST /recommendations/{rec_id}/approve`
**Description**: Approve or reject a recommendation  
**Request Body**:
```json
{
  "approved": true,
  "reason": "Optional reason"
}
```

#### `GET /recommendations/{rec_id}/view`
**Description**: Mark recommendation as viewed

---

## Guardrails & Safety

### Consent Management
- **Requirement**: 100% compliance - no recommendations to non-consented users
- **Implementation**: Database foreign key constraints + API-level checks
- **Audit**: All consent decisions logged with timestamps

### Content Safety
- **Prohibited Patterns**: Regex-based detection of financial shaming language
  - Patterns: "you're stupid", "always waste", "pathetic", "you deserve this debt"
- **Positive Framing**: Automatic rewriting of negative language
- **Disclaimers**: Required disclaimers injected by content type
  - Partner offers: "This is a partner offer. We may receive compensation if you apply."
  - Calculators: "Results are estimates only. Consult a financial advisor for personalized advice."
  - Articles: "This content is for educational purposes only and does not constitute financial advice."

### Rate Limiting
- Per-user rate limiting (configurable)
- Per-endpoint rate limiting
- Logging of rate limit violations

### Eligibility Checking
- Minimum income requirements
- Minimum credit score requirements
- Required account types
- Excluded products (user shouldn't already have)
- Content expiration (max_age_days)

---

## Deployment Architecture

### MVP Deployment (Single Server)

```
┌─────────────────────────────────────────────────────────────┐
│                    Single Server Deployment                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │   Streamlit │  │   FastAPI    │  │      SQLite         │  │
│  │      UI     │  │     API      │  │     Database        │  │
│  │   :8501     │  │    :8000     │  │   spend_sense.db    │  │
│  └─────────────┘  └──────────────┘  └─────────────────────┘  │
│         │                 │                     │            │
│         └─────────────────┼─────────────────────┘            │
│                           │                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Shared File System                         │  │
│  │   • Database files                                      │  │
│  │   • Content catalog                                     │  │
│  │   • Configuration files                                 │  │
│  │   • Log files                                           │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Development Environment
- **Docker**: Multi-stage builds with Colima support
- **Hot Reloading**: Code changes instantly reflected
- **Volume Mounting**: Source code, data, configs mounted for development
- **Makefile**: Common commands (`make up`, `make shell`, `make test`)

### Production Scaling Path
- **Phase 1**: SQLite (MVP) - supports <1000 users
- **Phase 2**: PostgreSQL - when concurrent users >100
- **Phase 3**: Event Sourcing - for enterprise scale

---

## Evaluation Metrics

### Coverage Metrics
- **User Coverage**: % of users who received recommendations
- **Persona Coverage**: % distribution across personas
- **Content Coverage**: % of content catalog used

### Quality Metrics
- **Avg Recommendations per User**: Average number of recommendations
- **Recommendation Diversity**: Average unique content types per user
- **Rationale Quality**: % of recommendations with rationales

### Performance Metrics
- **95th Percentile Computation Time**: P95 recommendation generation time
- **Error Rate**: % of users with signals but no recommendations
- **Data Quality Impact**: Correlation between data quality and recommendation quality

### Business Metrics
- **Partner Offer Rate**: % of recommendations that are partner offers
- **Educational Content Rate**: % that are educational (articles, checklists, calculators)

### Guardrails Metrics
- **Consent Compliance**: % of recommendations to consented users only (must be 100%)
- **Eligibility Compliance**: % of recommendations meeting eligibility criteria

---

## Content Strategy

### Content Types
1. **Articles**: Educational content (12+ reading time)
2. **Checklists**: Actionable steps (5-10 reading time)
3. **Calculators**: Interactive tools (5 reading time)
4. **Partner Offers**: Financial product recommendations

### Content Catalog
- **Initial Size**: 20+ items
- **Coverage**: All personas and signal triggers represented
- **Priority Scores**: 0.0-10.0 (higher = more important)
- **Eligibility Requirements**: Income, credit score, account types

### Rationale Templates
- Persona-based opening: "Based on your financial profile ({persona_name})"
- Trigger explanation: "because {trigger_explanation}"
- Specific signal values embedded: "your credit utilization is {X}%"

---

## Testing Strategy

### Unit Tests
- **Phase 1**: Signal schema, database operations, data generation
- **Phase 2**: Persona classifier (17 tests), signal mapper (11 tests), guardrails (9 tests), recommendation engine (11 tests), content schema (10 tests), integration (6 tests)
- **Phase 3**: Evaluation metrics (12 tests)

### Integration Tests
- End-to-end pipeline: Data generation → Loading → Signal computation → Recommendation generation
- API endpoint testing
- Guardrails compliance testing

### Manual Testing
- Comprehensive testing manual with step-by-step validation
- Test checkpoints after each phase
- Performance validation with 50-100 users

---

## Future Considerations

### Scalability
- Migration from SQLite to PostgreSQL
- Event-driven architecture for real-time processing
- Microservices decomposition when needed

### Features
- Real-time signal computation (currently batch)
- Multi-channel delivery (email, SMS, push)
- A/B testing framework for content
- Headless CMS integration
- Localization support

### MLOps
- Model training pipelines
- Model versioning and deployment
- Performance monitoring and alerting

---

## Appendix

### Signal Triggers

**Credit Triggers**:
- `HIGH_CREDIT_UTILIZATION`: credit_utilization_max >= 0.5
- `HAS_INTEREST_CHARGES`: has_interest_charges == true
- `IS_OVERDUE`: is_overdue == true
- `MINIMUM_PAYMENT_ONLY`: minimum_payment_only == true

**Income Triggers**:
- `VARIABLE_INCOME`: income_pay_gap > 45
- `LOW_CASH_BUFFER`: cash_flow_buffer < 1.0
- `HIGH_INCOME_VARIABILITY`: income_variability > 0.3

**Subscription Triggers**:
- `MANY_SUBSCRIPTIONS`: subscription_count >= 3
- `HIGH_SUBSCRIPTION_SPEND`: monthly_subscription_spend >= 50
- `HIGH_SUBSCRIPTION_SHARE`: subscription_share >= 0.10

**Savings Triggers**:
- `POSITIVE_SAVINGS`: monthly_savings_inflow > 0
- `NEGATIVE_SAVINGS_GROWTH`: savings_growth_rate < 0
- `LOW_EMERGENCY_FUND`: emergency_fund_months < 3

**Data Quality Triggers**:
- `INSUFFICIENT_DATA`: insufficient_data == true

### Persona Priorities
1. High Utilization (Priority 1) - Most urgent
2. Variable Income (Priority 2) - Time-sensitive
3. Subscription-Heavy (Priority 3) - Cost optimization
4. Savings Builder (Priority 4) - Growth opportunity
5. Insufficient Data (Priority 999) - Fallback

---

**Document Status**: Reconstructed from implementation documentation  
**Completeness**: Based on Architecture Guide, Implementation Phases 1-3, Testing Manual, Recommendation Engine Reference  
**Gaps**: May be missing original PRD details not reflected in implementation docs

