# SpendSense Decision Log

**Purpose**: Document key architectural and design decisions made during development  
**Last Updated**: November 6, 2025

---

## Overview

This document captures the rationale behind major technical and product decisions in SpendSense. Each decision includes the context, options considered, chosen approach, and trade-offs.

---

## 1. Database Choice: SQLite vs PostgreSQL

**Decision**: Use SQLite for MVP, design for PostgreSQL migration

**Context**: 
- MVP needs to support 50-100 users for beta testing
- Single-server deployment for simplicity
- No concurrent write requirements initially

**Options Considered**:
1. **SQLite**: File-based, zero configuration, sufficient for <1000 users
2. **PostgreSQL**: Production-grade, supports concurrent writes, requires setup
3. **MySQL**: Similar to PostgreSQL, less common in Python ecosystem

**Chosen Approach**: SQLite with PostgreSQL-compatible schema design

**Rationale**:
- SQLite is perfect for MVP: zero configuration, file-based, sufficient performance
- Schema designed with PostgreSQL migration in mind (standard SQL, no SQLite-specific features)
- Can migrate to PostgreSQL when concurrent users >100 or need multi-server deployment

**Trade-offs**:
- ✅ Pros: Fast setup, no database server needed, perfect for development
- ⚠️ Cons: Limited concurrent writes, not suitable for production scale

**Migration Path**: 
- When needed, swap connection string and run PostgreSQL schema
- All queries use standard SQL (no SQLite-specific syntax)

---

## 2. Persona Prioritization Logic

**Decision**: Priority-based tie-breaking (lower number = higher priority)

**Context**: 
- Users can match multiple personas
- Need deterministic way to assign single persona
- Some personas are more urgent than others

**Options Considered**:
1. **Priority-based**: Assign persona with lowest priority number
2. **Confidence-based**: Assign persona with highest confidence score
3. **First-match**: Assign first persona that matches (order-dependent)
4. **All-matches**: Assign all matching personas (complexity)

**Chosen Approach**: Priority-based with confidence as tie-breaker

**Rationale**:
- Priority reflects business urgency (credit issues > subscription optimization)
- Deterministic and explainable
- Confidence score used when priorities are equal

**Priority Order**:
1. High Utilization (credit issues - most urgent)
2. Variable Income (cash flow problems - time-sensitive)
3. Subscription-Heavy / Fee Fighter (cost optimization - less urgent)
4. Savings Builder (growth opportunity - least urgent)
5. Insufficient Data (fallback - lowest priority)

**Trade-offs**:
- ✅ Pros: Clear business logic, easy to explain, deterministic
- ⚠️ Cons: Users matching multiple personas only get one (by design)

---

## 3. Insufficient Data as Fallback Persona

**Decision**: Use "Insufficient Data" as system fallback, not a behavioral persona

**Context**:
- Original PRD requires 5 personas
- Some users have low data quality or no matching signals
- Need graceful degradation

**Options Considered**:
1. **Insufficient Data fallback**: System resilience persona (current)
2. **5th behavioral persona**: Fee Fighter, Debt Avalanche, etc.
3. **No persona assignment**: Return null/error

**Chosen Approach**: Insufficient Data as fallback + 5th behavioral persona (Fee Fighter)

**Rationale**:
- System needs fallback for edge cases (low data quality, no matches)
- But also needs 5th meaningful behavioral persona per original PRD
- Fee Fighter addresses real user pain point (avoidable bank fees)

**Trade-offs**:
- ✅ Pros: System resilience + complete persona coverage
- ⚠️ Cons: Two "5th personas" (fallback + behavioral) - clarified in docs

---

## 4. Content Catalog Structure

**Decision**: JSON file with Pydantic validation, not database table

**Context**:
- Content needs to be versioned and auditable
- Non-technical users may need to update content
- Content changes frequently during MVP

**Options Considered**:
1. **JSON file**: Version-controlled, easy to edit, requires validation
2. **Database table**: Structured, queryable, requires migrations
3. **Headless CMS**: Production-ready, overkill for MVP

**Chosen Approach**: JSON file with Pydantic schema validation

**Rationale**:
- JSON is human-readable and version-controllable
- Pydantic ensures type safety and validation
- Can migrate to database/CMS later without changing recommendation engine

**Trade-offs**:
- ✅ Pros: Simple, version-controlled, easy to audit changes
- ⚠️ Cons: Requires file reload on changes, not real-time updates

**Future Migration**: 
- When content team grows, migrate to database or headless CMS
- Recommendation engine interface remains unchanged

---

## 5. No Authentication for MVP

**Decision**: User ID tracking only, no authentication system

**Context**:
- MVP is for beta testing with trusted users
- Focus on core recommendation logic, not security infrastructure
- Can add auth later when moving to production

**Options Considered**:
1. **No auth**: User ID only (current)
2. **Basic auth**: Simple username/password
3. **OAuth**: Production-ready, complex setup
4. **API keys**: Simple but requires key management

**Chosen Approach**: User ID tracking only

**Rationale**:
- MVP goal is to validate recommendation quality, not security
- Beta users are developers/trusted testers
- Adding auth would delay core feature development

**Trade-offs**:
- ✅ Pros: Fast development, no auth complexity
- ⚠️ Cons: Not production-ready, users can access any user_id

**Production Path**:
- Add OAuth or API key authentication
- Add user session management
- Add rate limiting per authenticated user

---

## 6. Streamlit for Operator Dashboard

**Decision**: Use Streamlit for operator view, not custom web framework

**Context**:
- Need dashboard quickly for MVP
- Operators are internal, not end-users
- Focus on functionality over custom UI

**Options Considered**:
1. **Streamlit**: Rapid development, Python-native, limited customization
2. **React + FastAPI**: Full control, requires frontend development
3. **Dash (Plotly)**: Python-native, more customization than Streamlit
4. **Jupyter Notebooks**: Quick but not production-ready

**Chosen Approach**: Streamlit

**Rationale**:
- Fastest path to working dashboard
- Python-native (no separate frontend codebase)
- Sufficient for internal operator use
- Can rebuild in React later if needed

**Trade-offs**:
- ✅ Pros: Rapid development, single codebase, good for MVP
- ⚠️ Cons: Limited UI customization, not ideal for end-user experience

**Future Path**:
- Keep Streamlit for operator view
- Build separate end-user interface (React, mobile app, etc.)

---

## 7. Docker Deployment Approach

**Decision**: Single-container monolithic deployment for MVP

**Context**:
- Need consistent development and deployment environment
- Single server deployment for simplicity
- Fast iteration cycles

**Options Considered**:
1. **Single container**: All services in one container (current)
2. **Multi-container**: Separate containers for API, dashboard, database
3. **Kubernetes**: Production-ready, overkill for MVP
4. **Local only**: No containerization, direct Python execution

**Chosen Approach**: Single container with docker-compose

**Rationale**:
- Simplest deployment model
- Fast development iteration
- Easy to understand and debug
- Can split into microservices later

**Trade-offs**:
- ✅ Pros: Simple, fast, easy to debug
- ⚠️ Cons: Not scalable, all services share resources

**Production Path**:
- Split into separate containers (API, dashboard, database)
- Add orchestration (Kubernetes, Docker Swarm)
- Add monitoring and logging infrastructure

---

## 8. Synthetic Data Only (No Plaid Integration)

**Decision**: Use synthetic data generator, no real financial data integration

**Context**:
- MVP needs realistic test data
- Real financial APIs (Plaid, Yodlee) require compliance, contracts, costs
- Focus on recommendation logic, not data ingestion

**Options Considered**:
1. **Synthetic data**: Faker-based generator (current)
2. **Plaid integration**: Real financial data, requires compliance
3. **Manual CSV upload**: Realistic but manual
4. **Mock API**: Simulated Plaid responses

**Chosen Approach**: Synthetic data generator

**Rationale**:
- Fastest path to working system
- No compliance requirements for MVP
- Can test edge cases easily
- Realistic enough to validate recommendation logic

**Trade-offs**:
- ✅ Pros: Fast, no compliance, easy to test
- ⚠️ Cons: Not real user data, may miss edge cases

**Production Path**:
- Integrate Plaid or similar financial data provider
- Add compliance (SOC 2, data encryption)
- Add real-time data sync

---

## 9. Recommendation Rationale Templates

**Decision**: Template-based rationale generation with signal value substitution

**Context**:
- Every recommendation needs "because" explanation
- Rationales must be personalized with actual signal values
- Need to maintain consistency and tone

**Options Considered**:
1. **Templates**: String templates with variable substitution (current)
2. **LLM generation**: GPT/Claude for natural language (complex, expensive)
3. **Rule-based**: If-then rules for rationale generation
4. **Hybrid**: Templates + LLM for complex cases

**Chosen Approach**: Template-based with signal substitution

**Rationale**:
- Fast and deterministic
- Consistent tone and quality
- Easy to audit and modify
- No external API dependencies

**Trade-offs**:
- ✅ Pros: Fast, consistent, auditable, no cost
- ⚠️ Cons: Less natural language, requires template maintenance

**Future Path**:
- Keep templates for MVP
- Consider LLM enhancement for complex cases (optional)

---

## 10. No End-User UI in Initial MVP

**Decision**: Operator dashboard only, end-user UI added in Phase 4A

**Context**:
- Original PRD requires end-user experience
- Initial implementation focused on core logic
- README incorrectly stated "no end-user UI needed"

**Options Considered**:
1. **Operator only**: Internal dashboard (initial approach - incorrect)
2. **End-user UI first**: User-facing interface before operator view
3. **Both simultaneously**: Parallel development (slower)

**Chosen Approach**: Operator first, then end-user UI (Phase 4A)

**Rationale**:
- Core recommendation logic needed first
- Operator view needed to validate system
- End-user UI can reuse same API endpoints

**Trade-offs**:
- ✅ Pros: Focused development, API-first design
- ⚠️ Cons: Delayed end-user experience (now addressed in Phase 4A)

**Current Status**: End-user UI implemented in Phase 4A as "User View" page

---

## Summary

Key principles that guided decisions:
1. **Speed over sophistication**: MVP prioritizes working system over perfect architecture
2. **API-first design**: All functionality exposed via API, UI consumes API
3. **Migration-friendly**: Design allows easy migration to production technologies
4. **Explainability**: Every decision should be explainable and auditable
5. **Incremental complexity**: Start simple, add sophistication as needed

**Next Review**: After production deployment or major architecture changes

