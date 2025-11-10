# SpendSense Decision Log

**Purpose**: Document key architectural and design decisions made during development  
**Last Updated**: November 10, 2025

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

## 11. Railway Deployment Abandoned - Local-Only Development

**Decision**: Abandon Railway deployment, focus on local-only development

**Context**:

- Initial deployment steps taken on Railway (free tier)
- Encountered multiple issues: PORT environment variable, container lifecycle, data persistence
- Requirements specify local deployment for MVP
- Beta users are developers who can run locally

**Options Considered**:

1. **Continue Railway deployment**: Fix issues, maintain production-like environment
2. **Local-only**: Docker-based local development, simpler setup
3. **Hybrid**: Local dev, Railway for demos

**Chosen Approach**: Local-only with Docker/Colima

**Rationale**:

- Requirements specify local deployment
- Faster iteration without deployment overhead
- Fewer moving parts (no Railway-specific configuration)
- Beta users are developers comfortable with local setup
- Can revisit deployment later if needed

**Trade-offs**:

- ✅ Pros: Simpler, faster iteration, no deployment issues
- ⚠️ Cons: Not publicly accessible, requires local setup

**Status**: Railway deployment documentation preserved for future reference, but development focused on local-only

---

## 12. Docker with Colima for macOS Development

**Decision**: Use Docker via Colima instead of Docker Desktop GUI

**Context**:

- macOS development environment
- Docker Desktop requires GUI and more resources
- Need CLI-based Docker daemon for automation

**Options Considered**:

1. **Docker Desktop**: GUI-based, easy setup
2. **Colima**: CLI-based, lighter weight, better for automation
3. **No Docker**: Direct Python execution (inconsistent environments)

**Chosen Approach**: Colima + docker-compose

**Rationale**:

- CLI-based daemon works better with Makefile automation
- Lighter weight than Docker Desktop
- Consistent with development workflow
- Easy to start/stop: `colima start`

**Trade-offs**:

- ✅ Pros: CLI-friendly, lighter, better for automation
- ⚠️ Cons: Requires `colima start` before Docker commands

**Implementation**: Updated README with Colima setup instructions

---

## 13. No Password Hashing for Development/Demo

**Decision**: Skip password hashing for remainder of development and demo

**Context**:

- MVP is for development and demo purposes
- Beta users are trusted developers
- Focus on core features, not security infrastructure

**Options Considered**:

1. **No password hashing**: Plain text or simple auth (chosen)
2. **Full password hashing**: bcrypt/argon2 (production-ready)
3. **No auth at all**: User ID only (already decided)

**Chosen Approach**: No password hashing for dev/demo

**Rationale**:

- Development/demo context doesn't require production security
- Saves development time
- Can add proper hashing before production

**Trade-offs**:

- ✅ Pros: Faster development, simpler setup
- ⚠️ Cons: Not secure, only for dev/demo

**Production Path**: Implement proper password hashing (bcrypt/argon2) before production

---

## 14. Docker for All Development (Not Just Deployment)

**Decision**: Use Docker for development iteration, not just deployment

**Context**:

- Need consistent development environment
- Fast iteration cycles important
- Want to avoid "works on my machine" issues

**Options Considered**:

1. **Docker for everything**: Dev and deployment (chosen)
2. **Local Python + Docker for deployment**: Faster local iteration
3. **Docker only for deployment**: Inconsistent dev environments

**Chosen Approach**: Docker for all development

**Rationale**:

- Consistent environment across team
- Same environment for dev and deployment
- Fast enough iteration with volume mounts
- Can use `make shell` for quick access

**Trade-offs**:

- ✅ Pros: Consistency, same as production
- ⚠️ Cons: Slightly slower than native Python (acceptable)

**Implementation**: Makefile commands (`make up`, `make shell`, `make test`) all use Docker

---

## 15. Persona 6: Fraud Risk Implementation

**Decision**: Add 6th persona "Fraud Risk" to address fraud detection requirements

**Context**:

- Original PRD mentions fraud risk persona
- Synthetic data generator wasn't creating users with this profile
- Need to demonstrate fraud detection capabilities

**Options Considered**:

1. **Add to data generator**: Create users with fraud patterns (chosen)
2. **Skip for MVP**: Only implement 5 personas
3. **Manual test data**: Create fraud users manually

**Chosen Approach**: Update data generator to create users with fraud risk persona

**Rationale**:

- Required by PRD
- Demonstrates fraud detection functionality
- Needed for complete persona coverage

**Trade-offs**:

- ✅ Pros: Complete persona coverage, demonstrates fraud detection
- ⚠️ Cons: Additional complexity in data generator

**Implementation**: Updated `src/ingest/data_generator.py` to generate users with fraud patterns

---

## 16. Tailored "Why This Matters" Rationales

**Decision**: Make recommendation rationales tailored to specific signals, not generic

**Context**:

- Initial implementation had identical "Why this matters" text across recommendations
- User feedback: rationales should match article content and user's specific signals
- Example: Credit card article should mention credit utilization, not subscriptions

**Options Considered**:

1. **Tailored rationales**: Match article type to relevant signals (chosen)
2. **Generic rationales**: Same text for all (initial approach)
3. **LLM-generated**: Dynamic generation (too complex for MVP)

**Chosen Approach**: Template-based rationales that match article type to relevant user signals

**Rationale**:

- More personalized and relevant
- Better user experience
- Still deterministic and auditable
- No external API dependencies

**Trade-offs**:

- ✅ Pros: More relevant, better UX, still fast
- ⚠️ Cons: Requires template maintenance

**Implementation**: Updated recommendation engine to filter signals by article type when generating rationales

---

## 17. Consent Boolean Field with Realistic Distribution

**Decision**: Add explicit consent boolean field, set to 80-90% consent rate (not 100%)

**Context**:

- Dashboard showed 100% consent rate (unrealistic)
- Need to track user consent for recommendations
- Should reflect realistic consent distribution

**Options Considered**:

1. **Boolean field with 80-90% true**: Realistic distribution (chosen)
2. **100% consent**: Unrealistic, all users opted in
3. **No consent tracking**: Can't enforce consent requirements

**Chosen Approach**: Add `consent` boolean field, pre-set most to true but some to false

**Rationale**:

- Realistic for testing and demos
- Demonstrates consent enforcement
- Required for guardrails compliance

**Trade-offs**:

- ✅ Pros: Realistic, demonstrates consent enforcement
- ⚠️ Cons: Need to ensure recommendations respect consent

**Implementation**: Added `consent` field to users table, updated data generator to set 80-90% to true

---

## 18. Decision Trace Auditability

**Decision**: Implement full decision trace logging for every recommendation

**Context**:

- Auditability is a requirement
- Need to show how each recommendation was generated
- Operators need to understand recommendation logic

**Options Considered**:

1. **Full decision trace**: Log all 7 steps of recommendation pipeline (chosen)
2. **Summary only**: Just final rationale
3. **No trace**: Can't audit recommendations

**Chosen Approach**: Complete decision trace showing persona classification, signal mapping, deduplication, filtering, eligibility, scoring, and rationale generation

**Rationale**:

- Required for auditability
- Helps operators understand recommendations
- Enables debugging and improvement
- Stored in database for review

**Trade-offs**:

- ✅ Pros: Full auditability, debuggable, transparent
- ⚠️ Cons: Additional storage, more complex data model

**Implementation**: Added `decision_trace` JSON field to recommendations table, updated recommendation engine to generate traces

---

## 19. Fresh Recommendations (Not Just Pre-Computed)

**Decision**: Support both pre-computed and on-demand fresh recommendations

**Context**:

- Initial implementation only had pre-computed recommendations
- Users may want fresh recommendations based on latest data
- Need flexibility for different use cases

**Options Considered**:

1. **Both pre-computed and fresh**: Maximum flexibility (chosen)
2. **Pre-computed only**: Faster, but stale
3. **Fresh only**: Always up-to-date, but slower

**Chosen Approach**: Support both - pre-computed for performance, fresh on-demand for accuracy

**Rationale**:

- Pre-computed: Fast display, good for initial load
- Fresh: Up-to-date, good when data changes
- User choice based on needs

**Trade-offs**:

- ✅ Pros: Flexible, best of both worlds
- ⚠️ Cons: More complex implementation

**Implementation**: Added "Get New Recommendations" button in User View, generates fresh recommendations on-demand

---

## 20. Revoke Consent Button in User View

**Decision**: Add "Revoke Consent" button to end-user interface

**Context**:

- Users need ability to revoke consent
- Currently only operator can manage consent
- End-user interface should support consent management

**Options Considered**:

1. **Revoke consent button**: Simple toggle (chosen)
2. **No consent management in UI**: Operator-only
3. **Full consent management**: Grant and revoke (overkill for MVP)

**Chosen Approach**: Simple button that flips consent boolean

**Rationale**:

- Required for user control
- Simple implementation
- Demonstrates consent enforcement

**Trade-offs**:

- ✅ Pros: User control, simple
- ⚠️ Cons: Basic implementation (can enhance later)

**Implementation**: Added button in User View that updates consent field, recommendations respect consent status

---

## 21. User List with Persona Color Coding

**Decision**: Display user list with color-coded personas and legend

**Context**:

- Operator needs to quickly identify user personas
- Long list of users hard to scan
- Visual coding improves usability

**Options Considered**:

1. **Color-coded with legend**: Visual identification (chosen)
2. **Text labels only**: Less visual
3. **No persona display**: Harder to identify

**Chosen Approach**: Color outline on user buttons matching persona, with legend

**Rationale**:

- Quick visual identification
- Better UX for operators
- Easy to implement

**Trade-offs**:

- ✅ Pros: Better UX, quick identification
- ⚠️ Cons: Requires color scheme design

**Implementation**: Added persona-based color coding to user list in sidebar and User View

---

## 22. Demographic Data for Fairness Metrics

**Decision**: Add fake demographic data to demonstrate fairness functionality

**Context**:

- Fairness metrics section was empty (no demographic data)
- Need to demonstrate fairness analysis capabilities
- MVP needs to show all features working

**Options Considered**:

1. **Add fake demographic data**: Demonstrate functionality (chosen)
2. **Leave empty**: Can't demonstrate fairness
3. **Real demographic data**: Requires real user data (not available)

**Chosen Approach**: Add synthetic demographic data (age, gender, income bracket, etc.)

**Rationale**:

- Demonstrates fairness analysis
- Shows feature completeness
- Realistic enough for MVP

**Trade-offs**:

- ✅ Pros: Demonstrates feature, complete MVP
- ⚠️ Cons: Not real data (acceptable for MVP)

**Implementation**: Added demographic fields to users table, updated data generator to populate

---

## 23. Navigation Kept in Sidebar (Not Top Nav)

**Decision**: Keep navigation in sidebar, not move to top navigation

**Context**:

- Initial request to move nav to top
- After implementation, reverted back to sidebar
- Sidebar works better for Streamlit

**Options Considered**:

1. **Sidebar navigation**: Streamlit-native, better for many pages (chosen)
2. **Top navigation**: More traditional web app feel
3. **Both**: Redundant

**Chosen Approach**: Sidebar navigation (reverted from top nav)

**Rationale**:

- Streamlit's sidebar is well-suited for navigation
- Better for many pages
- More consistent with Streamlit patterns

**Trade-offs**:

- ✅ Pros: Streamlit-native, better UX for many pages
- ⚠️ Cons: Less traditional web app feel (acceptable)

**Implementation**: Kept `st.sidebar` navigation, removed top nav attempt

---

## 24. Documentation Preference: Chat Over Docs

**Decision**: Prefer chat explanations over document creation unless explicitly requested

**Context**:

- AI was creating documentation files without being asked
- User prefers chat explanations for most things
- Documents should only be created when explicitly requested

**Options Considered**:

1. **Chat explanations**: Quick, conversational (chosen)
2. **Always create docs**: More permanent, but creates clutter
3. **Ask first**: Check before creating docs

**Chosen Approach**: Explain in chat unless documentation is explicitly requested

**Rationale**:

- Faster communication
- Less file clutter
- Documents when needed for handoff or reference

**Trade-offs**:

- ✅ Pros: Faster, less clutter, more conversational
- ⚠️ Cons: Less permanent record (but can create docs when needed)

**Implementation**: Updated AI_TOOLS.md to note this preference

---

## Summary

Key principles that guided decisions:

1. **Speed over sophistication**: MVP prioritizes working system over perfect architecture
2. **API-first design**: All functionality exposed via API, UI consumes API
3. **Migration-friendly**: Design allows easy migration to production technologies
4. **Explainability**: Every decision should be explainable and auditable
5. **Incremental complexity**: Start simple, add sophistication as needed

**Next Review**: After production deployment or major architecture changes
