# SpendSense - Explainable Financial Education Platform

## 📖 Overview

**SpendSense** is an explainable financial education platform that analyzes transaction data to detect behavioral patterns, assign financial personas, and deliver personalized recommendations with clear "because" rationales.

### Key Features

- **Behavioral Signal Detection**: Automatically detects credit utilization, subscription spending, income patterns, and savings behavior from transaction data
- **Persona Classification**: Assigns users to one of 5 financial personas (High Utilization, Variable Income, Subscription-Heavy, Savings Builder, Fee Fighter)
- **Personalized Recommendations**: Generates 3-5 personalized financial education recommendations with explainable rationales
- **Operator Dashboard**: Streamlit-based dashboard for monitoring system health, user analytics, and recommendation quality
- **End-User Interface**: User-friendly view for displaying personalized recommendations
- **Comprehensive Evaluation**: Metrics for coverage, quality, performance, fairness, and relevance

### Core Value Proposition

Every recommendation includes a clear rationale explaining **why** it was made, using the user's actual financial data. For example: *"Because your credit card utilization is 75% (above the recommended 30%), reducing it could improve your credit score."*

---

## 🚀 Quick Start

### Prerequisites

- **macOS** (tested on macOS, Linux/WSL should work)
- **Docker** via Colima (lightweight Docker alternative)
- **Make** (comes with Xcode Command Line Tools)

### Installation

```bash
# 1. Install dependencies (one-time)
brew install docker colima docker-compose
xcode-select --install  # If make command not found

# 2. Start Docker daemon (first command every session)
colima start

# 3. Clone and initialize project
git clone <repository-url>
cd spend-sense
make init  # First-time setup (builds containers + initializes database)
```

### Daily Usage

```bash
# Start development environment
make up

# Access container shell
make shell

# Generate test data
make data  # or: python -m src.ingest.data_generator --users 50

# Run tests
make test

# Start API server (in container)
uvicorn src.api.routes:app --host 0.0.0.0 --port 8000 --reload

# Start operator dashboard (in another terminal)
make shell
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

**Access Points**:
- **API**: http://localhost:8000 (docs at http://localhost:8000/docs)
- **Operator Dashboard**: http://localhost:8501
- **User View**: http://localhost:8501 → Select "User View" from sidebar

---

## ⚡ Development Commands

### 🚀 Lightning Quick Start (30 seconds)

```bash
# Start Docker daemon (first command every session)
colima start

# First time setup (only run once)
make init

# Daily development (3 seconds)
make up && make shell
```

### Most Common Commands

```bash
make up         # Start development container (run first!)
make shell      # Access container shell
make test       # Run all tests (135+ tests)
make data       # Generate synthetic data (50 users)
make down       # Stop container
```

### Development Workflow

1. **Start environment**: `make up`
2. **Access shell**: `make shell`
3. **Edit code** in your IDE (changes are instantly reflected)
4. **Test changes**: `python -m src.ingest.data_generator --users 5`
5. **Run tests**: `make test` or `pytest tests/ -v`

**Note**: Code changes are instantly reflected - no rebuild needed! The container mounts your source code as a volume.

---

## 📚 Documentation

- **Operator Dashboard Guide**: `docs/OPERATOR_DASHBOARD_GUIDE.md` - Complete guide for using the Streamlit dashboard
- **Testing Manual**: `docs/Testing-Manual.md` - Manual testing procedures and quick smoke test
- **Architecture Guide**: `docs/Architecture-Guide.md` - System architecture and design decisions
- **Railway Deployment**: `docs/RAILWAY_QUICK_DEPLOY.md` - Quick deploy guide for Railway
- **Railway Port Fix**: `docs/RAILWAY_PORT_FIX.md` - Port configuration issue resolution
- **Implementation Guides**: `docs/misc/Implementation-Phase*.md` - Phase-by-phase implementation checklists

---

## 🆘 Troubleshooting

### Common Issues & Quick Fixes

**❌ "Cannot connect to the Docker daemon"**

```bash
# Solution: Start Colima first
colima start
```

**❌ "Docker not running! Run 'colima start' first" (but Colima says it's already running)**

This happens when Colima's process is running but the Docker daemon inside it isn't accessible. This is a common state issue.

```bash
# Solution: Restart Colima properly
colima stop    # Fully stop Colima
colima start   # Start it fresh

# Then verify Docker is accessible
docker ps      # Should work without errors
```

**Why this happens:** Colima's process can be running while the Docker daemon inside the VM isn't actually accessible. A full restart ensures the socket files are properly set up and the daemon is running.

**❌ "make: command not found"**

```bash
# Solution: Install Xcode Command Line Tools
xcode-select --install
```

**❌ "docker: command not found"**

```bash
# Solution: Install Docker CLI and Colima
brew install docker colima
colima start
```

**❌ "docker-compose: No such file or directory" or "make: docker-compose: No such file or directory"**

```bash
# Solution: Install docker-compose separately
# Note: Some Docker installations (especially Colima) don't include docker-compose
brew install docker-compose

# Verify installation
docker-compose --version
```

**❌ Container won't start or build fails**

```bash
# Solution: Clean rebuild
make clean && colima restart && make init
```

**❌ Code changes not reflecting**

```bash
# Solution: Check if container is running
make status
# If not running: make up
```

**❌ "service 'spendsense-app' is not running" or "make shell" fails**

```bash
# Solution: Start the container first
make up
# Then try make shell again
```

**❌ After changing docker-compose.yml or Dockerfile**

```bash
# Solution: Recreate container with new configuration
make down && make up
# This ensures new volume mounts and config are applied
```

**❌ "Port 8501 is already in use" (Streamlit)**

```bash
# Solution: Kill Streamlit processes
pkill -f streamlit

# Or kill process using port 8501 specifically
lsof -ti:8501 | xargs kill -9

# If running in container
docker-compose exec spendsense-app killall streamlit
```

---

## 🔨 Build, Test & Development

### Building

```bash
make build      # Build Docker containers
make init       # First-time setup (builds + initializes database)
```

### Testing

```bash
make test                    # Run full test suite (135+ tests)
make quick-test FILE=test_features.py  # Run single test file
pytest tests/ -v            # Run all tests with verbose output
pytest tests/ --cov=src     # Run with coverage report
```

### Validation

```bash
python scripts/validate_implementation.py  # Validates project structure
```

---

## 📖 Project Structure

```
spend-sense/
├── src/                    # Source code
│   ├── ingest/            # Data generation and loading
│   ├── features/          # Signal detection modules
│   ├── personas/          # Persona classification
│   ├── recommend/         # Recommendation engine
│   ├── guardrails/        # Safety and compliance
│   ├── api/               # FastAPI endpoints
│   ├── ui/                # Streamlit operator dashboard
│   ├── eval/              # Metrics and evaluation
│   └── db/                # Database connection management
├── tests/                 # Unit and integration tests
├── data/                  # Data files
│   ├── synthetic/         # Generated CSV files
│   └── content/           # Content catalog
├── db/                    # Database files
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

**Key Modules**:
- `src/ingest/` - Synthetic data generation and loading
- `src/features/` - Behavioral signal detection (credit, income, subscriptions, savings)
- `src/personas/` - Persona classification engine
- `src/recommend/` - Recommendation engine with rationale generation
- `src/guardrails/` - Consent management, content safety, eligibility checks
- `src/api/` - FastAPI REST endpoints
- `src/ui/` - Streamlit operator dashboard and user view
- `src/evaluation/` - Metrics and evaluation framework

---

## 🔌 API Usage

The SpendSense API runs on `http://localhost:8000` (when started with `uvicorn src.api.routes:app --reload`).

**Interactive API Docs**: http://localhost:8000/docs (Swagger UI)

#### Get User Profile
```bash
curl http://localhost:8000/profile/user_001?window=180d
```

Response:
```json
{
  "user_id": "user_001",
  "persona": {
    "persona_id": "high_utilization",
    "persona_name": "High Utilization",
    "priority": 1,
    "confidence": 0.85,
    "matched_criteria": ["Credit utilization 50% or higher"]
  },
  "signals": { ... },
  "triggers": ["high_credit_utilization", "has_interest_charges"]
}
```

#### Get Recommendations
```bash
curl http://localhost:8000/recommendations/user_001?max_recommendations=5
```

Response:
```json
{
  "user_id": "user_001",
  "recommendations": [
    {
      "rec_id": "uuid",
      "content_id": "credit_utilization_guide",
      "title": "Understanding Credit Utilization: The 30% Rule",
      "rationale": "Based on your financial profile (high utilization), because your credit card utilization is above 50%, your credit utilization is 75%.",
      "type": "article",
      "url": "/content/credit-utilization-guide"
    }
  ],
  "generated_at": "2025-11-06T12:00:00Z",
  "persona": "high_utilization"
}
```

#### Approve Recommendation
```bash
curl -X POST http://localhost:8000/recommendations/{rec_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "reason": "Looks good"}'
```

#### Mark Recommendation as Viewed
```bash
curl http://localhost:8000/recommendations/{rec_id}/view
```

#### Health Check
```bash
curl http://localhost:8000/health
```

---

## ⚠️ Limitations & Production Readiness

This is an MVP implementation with the following limitations:

### Data & Integration
- **Synthetic data only**: No real Plaid or financial data provider integration
- **No real-time updates**: Data is batch-processed, not real-time
- **Limited user scale**: Designed for 50-100 users, not production scale

### Security & Authentication
- **No authentication**: User ID tracking only, no login system
- **No encryption**: Data stored in plain SQLite database
- **Local only**: Not suitable for production deployment without security hardening

### Functionality
- **Simplified eligibility**: Missing real credit score checks (uses synthetic data)
- **Limited content catalog**: 20+ items vs. production needs 100+
- **No A/B testing**: Cannot test content variations
- **No personalization history**: Recommendations don't learn from user feedback

### Infrastructure
- **Single server**: Monolithic deployment, not horizontally scalable
- **SQLite database**: Limited concurrent writes, not production-grade
- **No monitoring**: Basic logging only, no APM or alerting

### Compliance
- **No SOC 2**: Not audited for security compliance
- **No data encryption**: Financial data not encrypted at rest
- **No GDPR compliance**: Missing data deletion and portability features

**Production Readiness**: This MVP is suitable for beta testing with trusted users only. Production deployment requires addressing all limitations above.
