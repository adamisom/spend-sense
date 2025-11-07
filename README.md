# SpendSense - Explainable Financial Education Platform

## ⚡ Super Fast Development with Docker

### 🚀 Lightning Quick Start (30 seconds)

```bash
# Start Docker daemon (first command every session)
colima start

# First time setup (only run once)
make init

# Daily development (3 seconds)
make up && make shell
```

### ⭐ Most Common Commands (Use These 90% of the Time)

```bash
make up         # Start development container (run first!)
make shell      # Access container shell (instant)
                #   To exit: type 'exit' or press Ctrl+D
make test       # Run all tests
make quick-run  # Quick validation (fastest)  
make data       # Generate synthetic data
make logs       # View container logs
make down       # Stop container (when done or before config changes)
```

### 🔥 Ultra-Fast Iteration Loop

```bash
# Start environment (once per session)
make up

# Inner loop (repeat constantly):
make shell
# Edit code in your IDE
python -m src.ingest.data_generator --users 5  # Test changes
exit  # Exit shell (or Ctrl+D)
# Repeat
```

### 🧪 Development Tips for Speed

**Hot Reloading**: Code changes are **instantly** reflected - no rebuild needed!

**Quick Tests**: Test specific modules without full suite:

```bash
make quick-test FILE=test_features.py
```

**Database Persistence**: Your data survives container restarts:

```bash
make down && make up  # Data is still there!
```

**Container Management**:
```bash
make up          # Start container (required before make shell)
make shell       # Access container shell
                 # To exit shell: type 'exit' or press Ctrl+D
                 # Note: Exiting shell doesn't stop the container
make down        # Stop container (clean shutdown)
make down && make up  # Restart container (use after docker-compose.yml changes)
docker-compose restart  # Quick restart without stopping (faster)
```

**IDE Integration**: Edit code normally - container picks up changes immediately.

**Reset Everything Fast**:

```bash
make reset-db  # Fresh database in 10 seconds
```

### 🔧 Advanced Development Workflow

```bash
# Start API server with hot reload
make up && make shell
uvicorn src.api.routes:app --host 0.0.0.0 --reload

# In another terminal, start dashboard
make shell
streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &

# In another terminal, run tests continuously
make shell  
pytest tests/ -v --watch
```

**Streamlit Process Management:**

```bash
# Kill all Streamlit processes on host
pkill -f streamlit

# Kill process using port 8501
lsof -ti:8501 | xargs kill -9

# Kill Streamlit in Docker container (if needed)
docker-compose exec spendsense-app killall streamlit
# or find and kill manually
docker-compose exec spendsense-app ps aux | grep streamlit
```

### 🎯 Performance Optimizations

- **Multi-stage Docker builds** - Only dependencies cached, not source code
- **Volume caching** - `cached` and `delegated` modes for macOS
- **Health checks** - Quick validation that environment is ready
- **Persistent volumes** - Database and logs survive restarts
- **Exclude **pycache**** - No Python bytecode sync slowdown

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

## Local Development (Alternative)

1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `python -m src.db.connection initialize`
4. `python -m src.ingest.data_generator --users 50`

## 🔨 Build, Test & Lint Commands

### Building

**Via Makefile (Docker):**

```bash
make build      # Build Docker containers (forced rebuild, no cache)
make init       # First-time setup (builds containers + initializes database)
```

**Docker Compose directly:**

```bash
docker compose build              # Build containers
docker compose build --no-cache   # Force rebuild without cache
```

### Testing

**Via Makefile (Docker):**

```bash
make test                    # Run full test suite with coverage
make quick-test FILE=test_features.py  # Run a single test file
```

**Direct (local or in container):**

```bash
pytest tests/ -v                                    # Run all tests
pytest tests/ --cov=src --cov-report=html          # Run with coverage report
pytest tests/ -v --tb=short                        # Short traceback format
```

**Validation scripts:**

```bash
python scripts/validate_implementation.py  # Validates project structure
python scripts/test_phase1.py              # Phase 1 validation tests
```

### Linting

**Note:** Linting tools are not currently configured. To add linting support:

**Recommended tools:**

- `black` - Code formatting
- `flake8` or `ruff` - Linting
- `mypy` - Type checking

**To set up linting:**

1. Add tools to `requirements.txt`
2. Add `make lint` and `make format` commands to `Makefile`
3. Optionally add pre-commit hooks

## Manual Test Checkpoints

See implementation checklist for detailed validation steps.

## Developer Documentation

### Project Structure

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

### Development Workflow

1. Generate synthetic data: `python -m src.ingest.data_generator --users 50`
2. Load data into database: `python scripts/load_data.py`
3. Run tests: `pytest tests/ -v`
4. Start API server: `uvicorn src.api.routes:app --reload`
5. Start operator dashboard: `streamlit run src/ui/operator_view.py`

### Beta Testing Notes

- All beta users are developers - no end-user UI needed
- Focus on API functionality and operator dashboard
- Use synthetic data only (no real financial data)
- Test with 50-100 synthetic users for performance validation
