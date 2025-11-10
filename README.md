# SpendSense - Explainable Financial Education Platform

**SpendSense** analyzes transaction data to detect behavioral patterns, assign financial personas, and deliver personalized recommendations with clear "because" rationales.

## 🚀 Quick Start (One Command)

```bash
# Prerequisites: Docker via Colima (macOS)
brew install docker colima docker-compose
colima start

# One-command setup (first time only)
make init && make up && make shell
```

Then in the container shell:
```bash
# Generate data, compute signals, and generate recommendations
python -m src.ingest.data_generator --users 50
python scripts/load_data.py
python scripts/compute_signals.py
python scripts/generate_recommendations.py --all

# Start operator dashboard
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

**Access**: http://localhost:8501

## 📋 Key Features

- **Behavioral Signal Detection**: Credit utilization, subscriptions, income patterns, savings behavior
- **Persona Classification**: 6 financial personas (High Utilization, Variable Income, Subscription-Heavy, Savings Builder, Fee Fighter, Fraud Risk)
- **Personalized Recommendations**: 3-5 recommendations with explainable rationales
- **Operator Dashboard**: Streamlit-based monitoring, analytics, and recommendation review
- **Decision Trace Auditability**: Full audit trail of recommendation generation process
- **End-User Interface**: User-friendly view for displaying recommendations

## 🛠️ Development Commands

```bash
make up         # Start development container
make shell      # Access container shell
make test       # Run all tests (131+ tests)
make data       # Generate synthetic data (50 users)
make down       # Stop container
```

## 📚 Documentation

- **Operator Dashboard Guide**: `docs/OPERATOR_DASHBOARD_GUIDE.md`
- **Architecture Guide**: `docs/Architecture-Guide.md`
- **Testing Manual**: `docs/Testing-Manual.md`
- **Railway Deployment**: `docs/RAILWAY_QUICK_DEPLOY.md` (initial steps taken, but deployment abandoned in favor of local-only per requirements)
- **Requirements Comparison**: `docs/REQUIREMENTS_COMPARISON.md`

## 🔌 API

**Base URL**: `http://localhost:8000`  
**Interactive Docs**: http://localhost:8000/docs

```bash
# Get user profile
curl http://localhost:8000/profile/user_001?window=180d

# Get recommendations
curl http://localhost:8000/recommendations/user_001?max_recommendations=5

# Health check
curl http://localhost:8000/health
```

## 🏗️ Project Structure

```
spend-sense/
├── src/
│   ├── ingest/          # Data generation and loading
│   ├── features/        # Signal detection modules
│   ├── personas/         # Persona classification
│   ├── recommend/      # Recommendation engine with decision traces
│   ├── guardrails/      # Safety and compliance
│   ├── api/             # FastAPI endpoints
│   ├── ui/              # Streamlit operator dashboard
│   ├── eval/            # Metrics and evaluation
│   └── db/              # Database connection management
├── tests/               # Unit and integration tests (131+ tests)
├── data/                # Data files and content catalog
├── db/                   # Database schema and migrations
└── scripts/             # Utility scripts
```

## 🔍 Decision Trace Auditability

Every recommendation includes a complete decision trace showing:
1. **Persona Classification**: Which persona was assigned and why
2. **Signal-to-Trigger Mapping**: How signals were converted to content triggers
3. **Deduplication**: Recently viewed content excluded
4. **Content Filtering**: Candidate items found
5. **Eligibility Check**: Items that passed eligibility requirements
6. **Scoring & Ranking**: Final scores and ranking logic
7. **Recommendation Generation**: Final rationale and match reasons

View decision traces in the **Recommendation Engine** page of the operator dashboard.

## ⚠️ Limitations

This is an MVP implementation:
- **Synthetic data only**: No real financial data provider integration
- **No authentication**: User ID tracking only
- **SQLite database**: Not production-grade for scale
- **Local deployment**: Not hardened for production security

**Production Readiness**: Suitable for beta testing with trusted users only.

## 🆘 Troubleshooting

**Docker not running:**
```bash
colima start
```

**Container won't start:**
```bash
make clean && colima restart && make init
```

**Code changes not reflecting:**
```bash
make down && make up  # Restart container
```

**Port 8501 in use:**
```bash
lsof -ti:8501 | xargs kill -9
```

## 📦 Deliverables

- ✅ Code repository (GitHub)
- ✅ Technical writeup (`docs/Architecture-Guide.md`)
- ✅ Documentation (`docs/`)
- ✅ Demo video / live presentation ready
- ✅ Performance metrics (`src/evaluation/`)
- ✅ Test cases (`tests/` - 131+ tests)
- ✅ Data model/schema (`db/schema.sql`)
- ✅ Evaluation report (`src/evaluation/`)

---

**Built with**: Python 3.9+, FastAPI, Streamlit, SQLite, Docker/Colima
