# SpendSense - Fast Development Commands
# Usage: make <command>

.PHONY: help build up down logs shell test clean init quick-test quick-run

# Default help command
help:
	@echo "🚀 SpendSense Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  colima start  - Start Docker daemon (first!)"
	@echo "  make init     - Initialize project (first time setup)"
	@echo "  make up       - Start development environment"
	@echo "  make shell    - Access container shell"
	@echo ""
	@echo "Development:"
	@echo "  make test     - Run tests"
	@echo "  make quick-test - Run single test file"
	@echo "  make logs     - View container logs"
	@echo "  make clean    - Clean up containers and volumes"
	@echo ""
	@echo "Data & API:"
	@echo "  make data     - Generate synthetic data"
	@echo "  make api      - Start FastAPI server"
	@echo "  make ui       - Start Streamlit dashboard"
	@echo ""
	@echo "Quick Actions:"
	@echo "  make quick-run - Test data generation (fastest)"
	@echo "  make reset-db  - Reset database with fresh data"
	@echo ""
	@echo "Troubleshooting:"
	@echo "  💡 See 'Cannot connect to Docker daemon'? Run: colima start"

# Fast initialization (only run once)
init:
	@echo "🏗️ Initializing SpendSense..."
	@echo "🔍 Checking if Docker daemon is running..."
	@docker info >/dev/null 2>&1 || { echo "❌ Docker not running! Run 'colima start' first"; exit 1; }
	docker compose build --parallel
	docker compose --profile init run --rm spendsense-init
	@echo "✅ Ready for development!"

# Start development environment (fast startup)
up:
	@echo "🚀 Starting development environment..."
	@docker info >/dev/null 2>&1 || { echo "❌ Docker not running! Run 'colima start' first"; exit 1; }
	docker compose up -d
	@echo "✅ Container ready! Use 'make shell' to access."

# Stop containers
down:
	docker compose down

# View logs (streaming)
logs:
	docker compose logs -f spendsense-app

# Access container shell (most common command)
shell:
	docker compose exec spendsense-app bash

# Run tests (full suite)
test:
	docker compose --profile testing run --rm spendsense-test

# Quick test (single file) - use like: make quick-test FILE=test_features.py
quick-test:
	docker compose exec spendsense-app pytest tests/$(FILE) -v --tb=short

# Generate data (fast)
data:
	docker compose exec spendsense-app python -m src.ingest.data_generator --users 50

# Load data to database
load:
	docker compose exec spendsense-app python scripts/load_data.py --validate

# Start API server with hot reload
api:
	docker compose exec spendsense-app uvicorn src.api.routes:app --host 0.0.0.0 --reload &

# Start Streamlit dashboard
ui:
	docker compose exec spendsense-app streamlit run src/ui/operator_view.py --server.address 0.0.0.0 &

# Quick run (fastest test) - just check if everything imports
quick-run:
	@echo "🧪 Quick validation test..."
	docker compose exec spendsense-app python -c "from src.features.schema import UserSignals; from src.db.connection import get_connection; print('✅ All core imports work!')"

# Reset database with fresh data
reset-db:
	@echo "🔄 Resetting database..."
	docker compose exec spendsense-app rm -f /app/db/spend_sense.db
	docker compose exec spendsense-app python -c "from src.db.connection import initialize_db; initialize_db()"
	docker compose exec spendsense-app python -m src.ingest.data_generator --users 50
	docker compose exec spendsense-app python scripts/load_data.py --validate
	@echo "✅ Database reset complete!"

# Clean up everything (nuclear option)
clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

# Build containers (forced rebuild)
build:
	docker compose build --no-cache --parallel

# Development status check
status:
	@echo "📊 SpendSense Development Status:"
	@echo ""
	@echo "🐳 Docker Status:"
	@docker info --format "Docker: {{.ServerVersion}}" 2>/dev/null || echo "Docker daemon not running"
	@echo ""
	@docker compose ps
	@echo ""
	@echo "📁 Volume Status:"
	@docker volume ls | grep spendsense || echo "No persistent volumes found"
	@echo ""
	@echo "🔍 Quick Health Check:"
	@docker compose exec spendsense-app python --version 2>/dev/null || echo "Container not running"

# Watch logs for specific service
watch-logs:
	docker compose logs -f --tail=50 spendsense-app

# Start colima (Docker daemon)
colima-start:
	@echo "🐳 Starting Colima Docker daemon..."
	colima start
	@echo "✅ Colima started!"

# Stop colima
colima-stop:
	@echo "🛑 Stopping Colima..."
	colima stop
	@echo "✅ Colima stopped!"

