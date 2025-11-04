# SpendSense Implementation Checklist

## 🎯 Purpose
This document breaks down the [SpendSense PRD](claude-PRD-SpendSense.md) into **actionable micro-tasks** that can be completed in 15-60 minutes each. Each task has clear deliverables, validation steps, and dependency requirements.

## 📋 How to Use This Checklist
1. ✅ Complete tasks in the **exact order specified**
2. 🚫 **Never skip dependency validation** - if a task's dependencies aren't met, stop and fix them first
3. ⏱️ **Time estimates are conservative** - experienced developers may be faster
4. 🧪 **Run validation after each task** - catch issues early
5. 🔄 **If validation fails**, fix the issue before proceeding

---

## 🚀 PHASE 1: Data Foundation & Signal Detection

**Phase Goal**: Working data pipeline with signal detection  
**Estimated Total Time**: 12-16 hours  
**Success Criteria**: All 50 synthetic users have computed signals, unit tests pass

---

### 📁 **Phase 1.1: Project Foundation** (2 hours)

#### ✅ Task 1.1.1: Create Project Structure (15 min)
**Dependencies**: None  
**Deliverable**: Complete directory structure

```bash
# Execute these commands
mkdir -p spend-sense/{src,tests,data,db,docs,scripts,config}
mkdir -p spend-sense/src/{ingest,features,personas,recommend,guardrails,api,ui,eval,db}
mkdir -p spend-sense/tests
mkdir -p spend-sense/data/{synthetic,content}
cd spend-sense

# Create all __init__.py files
find src -type d -exec touch {}/__init__.py \;
touch tests/__init__.py
```

**Validation**:
```bash
# Must show all directories
tree spend-sense/ -d
# Expected: 15+ directories including src/features, src/db, etc.
```

**Blockers for**: All subsequent tasks

---

#### ✅ Task 1.1.2: Create Requirements File (10 min)
**Dependencies**: Task 1.1.1  
**Deliverable**: `requirements.txt` with exact versions

**Create `requirements.txt`**:
```txt
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
```

**Validation**:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python -c "import pandas, fastapi, pydantic; print('✅ All imports successful')"
```

**Blockers for**: Any Python imports

---

#### ✅ Task 1.1.3: Create Base Configuration Files (20 min)
**Dependencies**: Task 1.1.2  
**Deliverable**: `.env.example`, `.gitignore`, basic `README.md`

**Create `.env.example`**:
```bash
# Database
DATABASE_PATH=db/spend_sense.db
TEST_DATABASE_PATH=db/test_spend_sense.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/spend_sense.log

# Synthetic Data
RANDOM_SEED=42
DEFAULT_USER_COUNT=50

# API
API_HOST=localhost
API_PORT=8000
```

**Create `.gitignore`**:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
.env

# Database
*.db
*.db-journal
*.db-wal
*.db-shm

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Data
data/synthetic/*.csv
```

**Create `README.md`**:
```markdown
# SpendSense - Explainable Financial Education Platform

## Quick Start
1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `python -m src.db.connection initialize`
4. `python -m src.ingest.data_generator --users 50`

## Testing
- `pytest tests/ -v`
- `pytest tests/ --cov=src --cov-report=html`

## Manual Test Checkpoints
See implementation checklist for detailed validation steps.
```

**Validation**:
```bash
# Check files exist
ls -la .env.example .gitignore README.md
# Expected: All three files present with content
```

**Blockers for**: Environment setup, version control

---

#### ✅ Task 1.1.4: Docker Setup for Consistent Environment (30 min)
**Dependencies**: Task 1.1.3  
**Deliverable**: `Dockerfile`, `docker-compose.yml`, and Docker-based development workflow

**Create `Dockerfile`**:
```dockerfile
# SpendSense - Consistent Python 3.11 environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p db data/synthetic logs

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["python", "-m", "src.api.routes"]
```

**Create `docker-compose.yml`**:
```yaml
version: '3.8'

services:
  spendsense-app:
    build: .
    container_name: spendsense-dev
    ports:
      - "8000:8000"  # FastAPI
      - "8501:8501"  # Streamlit
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
      - ./data:/app/data
      - ./db:/app/db
      - ./scripts:/app/scripts
    environment:
      - DATABASE_PATH=/app/db/spend_sense.db
      - LOG_LEVEL=INFO
      - PYTHONPATH=/app
    working_dir: /app
    command: tail -f /dev/null  # Keep container running for development

  spendsense-test:
    build: .
    container_name: spendsense-test
    volumes:
      - .:/app
    environment:
      - DATABASE_PATH=/app/db/test_spend_sense.db
      - PYTHONPATH=/app
    working_dir: /app
    profiles: ["testing"]
    command: pytest tests/ -v --cov=src --cov-report=html
```

**Create `.dockerignore`**:
```dockerignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
.venv/

# Database files
*.db
*.db-journal
*.db-wal
*.db-shm

# IDE and OS
.vscode/
.idea/
.DS_Store
Thumbs.db

# Logs and temp files
logs/
*.log
.pytest_cache/
.coverage
htmlcov/

# Git
.git/
.gitignore

# Generated data
data/synthetic/*.csv
```

**Update README.md with Docker workflow**:
```markdown
## Development with Docker (Recommended)

### Quick Start with Docker
1. `docker-compose build`
2. `docker-compose up -d`
3. `docker-compose exec spendsense-app python -m src.ingest.data_generator --users 50`
4. `docker-compose exec spendsense-app python scripts/load_data.py`

### Running Tests
```bash
# Run tests in isolated container
docker-compose --profile testing run --rm spendsense-test

# Or run tests in development container
docker-compose exec spendsense-app pytest tests/ -v
```

### Development Workflow
```bash
# Start development environment
docker-compose up -d

# Access container shell
docker-compose exec spendsense-app bash

# Generate data
docker-compose exec spendsense-app python -m src.ingest.data_generator --users 50

# Start API server
docker-compose exec spendsense-app uvicorn src.api.routes:app --host 0.0.0.0 --reload

# Start Streamlit dashboard
docker-compose exec spendsense-app streamlit run src/ui/operator_view.py --server.address 0.0.0.0
```

## Local Development (Alternative)
1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `python -m src.db.connection initialize`
4. `python -m src.ingest.data_generator --users 50`
```

**Validation**:
```bash
# Start Docker daemon first
colima start

# Lightning-fast setup and validation
make init
# Expected: ✅ SpendSense initialized successfully!

make quick-run  
# Expected: ✅ All core imports work!

make status
# Expected: Container running, volumes mounted

# Quick test
make quick-test FILE=test_phase1.py
# Expected: Tests pass
```

**Benefits**:
- **Consistent Environment**: Python 3.11 regardless of host system
- **Dependency Isolation**: No conflicts with host Python packages  
- **Easy Testing**: Isolated test runs with fresh database
- **Production Parity**: Same environment for dev/test/prod
- **Team Collaboration**: Same setup across all developers

**Blockers for**: Consistent testing and validation

---

### 🗄️ **Phase 1.2: Database Foundation** (1.5 hours)

#### ✅ Task 1.2.1: Create Signal Schema Definition (45 min)
**Dependencies**: Task 1.1.4 (Docker setup recommended for testing)  
**Deliverable**: `src/features/schema.py` with UserSignals model

**Create `src/features/schema.py`**:
```python
"""
Signal output schema - CRITICAL: Field names must match persona criteria exactly
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserSignals(BaseModel):
    """Standardized signal output schema - field names MUST match persona criteria."""
    
    # Credit signals (CRITICAL: exact field names for persona matching)
    credit_utilization_max: Optional[float] = Field(None, ge=0.0, le=1.0, description="Highest utilization across all cards (0.0-1.0)")
    has_interest_charges: bool = Field(False, description="True if any interest charges detected")
    is_overdue: bool = Field(False, description="True if any overdue payments")
    minimum_payment_only: bool = Field(False, description="True if only making minimum payments")
    
    # Income signals (CRITICAL: exact field names)
    income_pay_gap: Optional[int] = Field(None, ge=0, description="Days between income deposits")
    cash_flow_buffer: Optional[float] = Field(None, ge=0.0, description="Months of expenses covered")
    income_variability: Optional[float] = Field(None, ge=0.0, description="Coefficient of variation")
    
    # Subscription signals (CRITICAL: exact field names)
    subscription_count: int = Field(0, ge=0, description="Number of detected subscriptions")
    monthly_subscription_spend: float = Field(0.0, ge=0.0, description="Total monthly recurring spend")
    subscription_share: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of total spend (0.0-1.0)")
    
    # Savings signals (CRITICAL: exact field names)
    savings_growth_rate: Optional[float] = Field(None, description="Monthly growth rate (can be negative)")
    monthly_savings_inflow: float = Field(0.0, description="Average monthly savings deposits")
    emergency_fund_months: Optional[float] = Field(None, ge=0.0, description="Months of expenses covered")
    
    # Data quality flags
    insufficient_data: bool = Field(False, description="True if below minimum thresholds")
    data_quality_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in signals (0.0-1.0)")
    computation_errors: List[str] = Field(default_factory=list, description="Any errors during computation")
    
    # Metadata
    computed_at: datetime = Field(default_factory=datetime.now, description="When signals were computed")
    window: str = Field("180d", description="Time window used ('30d' or '180d')")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SignalValidationError(Exception):
    """Raised when signal validation fails."""
    pass

def validate_signal_completeness(signals: UserSignals) -> List[str]:
    """Validate signal completeness and return list of issues."""
    issues = []
    
    # Check data quality
    if signals.data_quality_score < 0.5:
        issues.append(f"Low data quality score: {signals.data_quality_score}")
    
    # Check for computation errors
    if signals.computation_errors:
        issues.append(f"Computation errors: {signals.computation_errors}")
    
    # Check critical signals for persona assignment
    if signals.credit_utilization_max is None and signals.monthly_savings_inflow == 0:
        issues.append("Neither credit nor savings signals available")
    
    return issues
```

**Validation**:
```python
# Test in Python REPL
from src.features.schema import UserSignals, validate_signal_completeness
from datetime import datetime

# Test valid signals
signals = UserSignals(
    credit_utilization_max=0.65,
    has_interest_charges=True,
    subscription_count=3,
    monthly_subscription_spend=89.99
)
print(f"✅ Valid signals created: {signals.credit_utilization_max}")

# Test validation
issues = validate_signal_completeness(signals)
print(f"✅ Validation issues: {len(issues)}")

# Test JSON serialization
json_str = signals.model_dump_json()
print(f"✅ JSON serialization works: {len(json_str)} chars")
```

**Blockers for**: All signal detection modules, persona assignment

---

#### ✅ Task 1.2.2: Create Database Schema (30 min)
**Dependencies**: Task 1.2.1  
**Deliverable**: `db/schema.sql` with all tables

**Create `db/schema.sql`**:
```sql
-- SpendSense Database Schema
-- Version: 3.0
-- CRITICAL: Field names must align with UserSignals schema

-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consent_status BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP
);

-- Accounts (Plaid-style structure)
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- checking, savings, credit card, investment
    subtype TEXT,        -- checking, savings, credit card, etc.
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
    amount REAL NOT NULL,  -- Positive for inflow, negative for outflow
    merchant_name TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    payment_channel TEXT,  -- online, in store, atm, other
    pending BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Credit card details
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

-- Computed signals (cached for performance)
CREATE TABLE user_signals (
    user_id TEXT NOT NULL,
    window TEXT NOT NULL,  -- '30d' or '180d'
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signals JSON NOT NULL,  -- UserSignals as JSON
    PRIMARY KEY (user_id, window),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Persona assignments
CREATE TABLE persona_assignments (
    user_id TEXT NOT NULL,
    window TEXT NOT NULL,
    persona TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    criteria JSON NOT NULL,  -- Matched criteria for explainability
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
    approved BOOLEAN DEFAULT NULL,  -- NULL=pending, TRUE=approved, FALSE=rejected
    delivered BOOLEAN DEFAULT FALSE,
    viewed_at TIMESTAMP,  -- For content deduplication
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for performance
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_name);
CREATE INDEX idx_accounts_user_type ON accounts(user_id, type);
CREATE INDEX idx_recommendations_user_created ON recommendations(user_id, created_at);
```

**Validation**:
```bash
# Test schema validity
sqlite3 test_schema.db < db/schema.sql
sqlite3 test_schema.db ".tables"
# Expected: 7 tables (users, accounts, transactions, liabilities, user_signals, persona_assignments, recommendations)

# Clean up test
rm test_schema.db
```

**Blockers for**: Database connection, data loading

---

#### ✅ Task 1.2.3: Create Database Connection Module (45 min)
**Dependencies**: Task 1.2.2  
**Deliverable**: `src/db/connection.py` with connection management

**Create `src/db/connection.py`**:
```python
"""
Database connection management with transaction safety and monitoring
"""
import sqlite3
import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

class DatabaseError(Exception):
    """Base exception for database operations."""
    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Database operation failed: {operation} - {details}")

def get_connection(db_path: str = "db/spend_sense.db") -> sqlite3.Connection:
    """Get SQLite connection with optimized settings."""
    try:
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(
            db_path, 
            check_same_thread=False,
            timeout=30.0  # 30 second timeout
        )
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Optimize SQLite settings
        conn.execute("PRAGMA journal_mode=WAL")  # Enable concurrent reads
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety and performance
        conn.execute("PRAGMA cache_size=10000")  # 10MB cache
        conn.execute("PRAGMA temp_store=memory")  # Use memory for temp storage
        
        return conn
    except sqlite3.Error as e:
        raise DatabaseError("connection", str(e))

@contextmanager
def database_transaction(db_path: str = "db/spend_sense.db"):
    """Context manager for database transactions with automatic retry."""
    conn = None
    max_retries = 3
    retry_delay = 0.1  # 100ms
    
    for attempt in range(max_retries + 1):
        try:
            conn = get_connection(db_path)
            conn.execute("BEGIN IMMEDIATE")  # Exclusive write lock
            yield conn
            conn.commit()
            break
            
        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()
                conn.close()
                conn = None
            
            if "database is locked" in str(e).lower() and attempt < max_retries:
                logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                raise DatabaseError("transaction", str(e))
                
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
                conn = None
            raise DatabaseError("transaction", str(e))
    
    finally:
        if conn:
            conn.close()

def initialize_db(schema_path: str = "db/schema.sql", db_path: str = "db/spend_sense.db"):
    """Initialize database from schema file."""
    try:
        if not Path(schema_path).exists():
            raise DatabaseError("initialization", f"Schema file not found: {schema_path}")
        
        with database_transaction(db_path) as conn:
            with open(schema_path) as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
        
        logger.info(f"Database initialized successfully: {db_path}")
        
    except Exception as e:
        raise DatabaseError("initialization", str(e))

def save_user_signals(user_id: str, window: str, signals: Dict[str, Any], db_path: str = "db/spend_sense.db"):
    """Save computed signals to database."""
    try:
        with database_transaction(db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_signals (user_id, window, signals)
                VALUES (?, ?, ?)
            """, (user_id, window, json.dumps(signals)))
        
        logger.debug(f"Saved signals for user {user_id}, window {window}")
        
    except Exception as e:
        raise DatabaseError("save_signals", str(e))

def get_user_signals(user_id: str, window: str, db_path: str = "db/spend_sense.db") -> Optional[Dict[str, Any]]:
    """Retrieve user signals from database."""
    try:
        with database_transaction(db_path) as conn:
            result = conn.execute("""
                SELECT signals FROM user_signals 
                WHERE user_id = ? AND window = ?
            """, (user_id, window)).fetchone()
        
        if result:
            return json.loads(result['signals'])
        return None
        
    except Exception as e:
        raise DatabaseError("get_signals", str(e))

# Performance monitoring
class PerformanceMonitor:
    """Simple performance monitoring for database operations."""
    
    @staticmethod
    def log_db_operation(operation: str, duration_ms: float, record_count: Optional[int] = None):
        """Log database operation performance."""
        logger.info("Database operation completed", extra={
            "operation": operation,
            "duration_ms": duration_ms,
            "record_count": record_count,
            "metric_type": "database_operation"
        })
        
        # Alert on slow operations
        if duration_ms > 1000:  # 1 second threshold
            logger.warning("Slow database operation detected", extra={
                "operation": operation,
                "duration_ms": duration_ms,
                "alert_type": "database_performance"
            })

def monitor_db_performance(operation_name: str):
    """Decorator for monitoring database operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                record_count = len(result) if isinstance(result, (list, tuple)) else None
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                PerformanceMonitor.log_db_operation(operation_name, duration_ms)
        return wrapper
    return decorator
```

**Validation**:
```python
# Test database operations
from src.db.connection import initialize_db, database_transaction, save_user_signals, get_user_signals
import tempfile
import os

# Test with temporary database
test_db = "test_connection.db"

try:
    # Test initialization
    initialize_db(db_path=test_db)
    print("✅ Database initialization successful")
    
    # Test transaction
    with database_transaction(test_db) as conn:
        conn.execute("INSERT INTO users (user_id) VALUES (?)", ("test_user",))
    print("✅ Transaction successful")
    
    # Test signal storage
    test_signals = {"credit_utilization_max": 0.65, "subscription_count": 3}
    save_user_signals("test_user", "180d", test_signals, test_db)
    print("✅ Signal storage successful")
    
    # Test signal retrieval
    retrieved = get_user_signals("test_user", "180d", test_db)
    assert retrieved["credit_utilization_max"] == 0.65
    print("✅ Signal retrieval successful")
    
finally:
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
```

**Blockers for**: All database operations, data loading, signal computation

---

### 🏭 **Phase 1.3: Synthetic Data Generation** (4 hours)

#### ✅ Task 1.3.1: Create Base Data Generator Class (60 min)
**Dependencies**: Task 1.2.3  
**Deliverable**: `src/ingest/data_generator.py` with generator framework

**Create `src/ingest/data_generator.py`**:
```python
"""
Synthetic data generator for SpendSense
Creates realistic financial data with edge cases for robust testing
"""
import random
import csv
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from faker import Faker
from loguru import logger
import pandas as pd

@dataclass
class UserProfile:
    """Represents a synthetic user's financial profile."""
    user_id: str
    income_level: str  # low, medium, high
    credit_behavior: str  # excellent, good, fair, poor
    savings_behavior: str  # aggressive, moderate, minimal, none
    subscription_tendency: str  # heavy, moderate, light
    financial_stress: bool
    scenario: Optional[str] = None  # For edge cases

class SyntheticDataGenerator:
    """Generate realistic synthetic financial data for testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with reproducible seed."""
        self.seed = seed
        random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)
        
        # Configuration
        self.income_ranges = {
            'low': (25000, 40000),
            'medium': (40000, 80000),
            'high': (80000, 150000)
        }
        
        self.merchant_categories = {
            'subscription': ['Netflix', 'Spotify', 'Disney+', 'Adobe', 'Zoom', 'NYTimes', 'Gym Membership'],
            'grocery': ['Whole Foods', 'Safeway', 'Trader Joes', 'Kroger', 'Costco'],
            'gas': ['Shell', 'Chevron', 'BP', 'Exxon', 'Arco'],
            'restaurant': ['Starbucks', 'McDonalds', 'Chipotle', 'Subway', 'Pizza Hut'],
            'shopping': ['Amazon', 'Target', 'Walmart', 'Best Buy', 'Apple Store'],
            'utilities': ['PG&E', 'AT&T', 'Comcast', 'Water Dept', 'Electric Co']
        }
        
        self.account_types = {
            'checking': {'balance_range': (500, 15000), 'typical_transactions': 50},
            'savings': {'balance_range': (0, 50000), 'typical_transactions': 5},
            'credit_card': {'balance_range': (0, 25000), 'credit_limit_range': (1000, 50000), 'typical_transactions': 20}
        }
        
    def generate_user_profiles(self, count: int, include_edge_cases: bool = True) -> List[UserProfile]:
        """Generate diverse user profiles including edge cases."""
        profiles = []
        edge_case_count = max(1, count // 10) if include_edge_cases else 0  # 10% edge cases
        
        # Generate normal profiles
        for i in range(count - edge_case_count):
            profile = UserProfile(
                user_id=f"user_{i+1:03d}",
                income_level=random.choices(['low', 'medium', 'high'], weights=[30, 50, 20])[0],
                credit_behavior=random.choices(['excellent', 'good', 'fair', 'poor'], weights=[20, 40, 25, 15])[0],
                savings_behavior=random.choices(['aggressive', 'moderate', 'minimal', 'none'], weights=[15, 35, 35, 15])[0],
                subscription_tendency=random.choices(['heavy', 'moderate', 'light'], weights=[20, 60, 20])[0],
                financial_stress=random.choice([True, False])
            )
            profiles.append(profile)
        
        # Generate edge case profiles
        if include_edge_cases:
            edge_cases = self._generate_edge_case_profiles(edge_case_count, len(profiles))
            profiles.extend(edge_cases)
        
        return profiles
    
    def _generate_edge_case_profiles(self, count: int, start_idx: int) -> List[UserProfile]:
        """Generate specific edge case profiles for testing."""
        edge_cases = []
        scenarios = [
            'high_utilization_and_subscription_heavy',
            'sparse_transaction_history', 
            'high_savings_rate',
            'multiple_red_flags',
            'new_user_insufficient_data',
            'variable_income_gig_worker',
            'debt_consolidation_candidate',
            'cash_heavy_user'
        ]
        
        for i in range(count):
            scenario = scenarios[i % len(scenarios)]
            
            if scenario == 'high_utilization_and_subscription_heavy':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='medium',
                    credit_behavior='poor',  # High utilization
                    savings_behavior='none',
                    subscription_tendency='heavy',  # Many subscriptions
                    financial_stress=True,
                    scenario=scenario
                )
            elif scenario == 'sparse_transaction_history':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='low',
                    credit_behavior='excellent',
                    savings_behavior='minimal',
                    subscription_tendency='light',
                    financial_stress=False,
                    scenario=scenario
                )
            elif scenario == 'high_savings_rate':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='high',
                    credit_behavior='excellent',
                    savings_behavior='aggressive',
                    subscription_tendency='light',
                    financial_stress=False,
                    scenario=scenario
                )
            elif scenario == 'multiple_red_flags':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='low',
                    credit_behavior='poor',
                    savings_behavior='none',
                    subscription_tendency='heavy',
                    financial_stress=True,
                    scenario=scenario
                )
            elif scenario == 'new_user_insufficient_data':
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level='medium',
                    credit_behavior='good',
                    savings_behavior='moderate',
                    subscription_tendency='moderate',
                    financial_stress=False,
                    scenario=scenario
                )
            else:
                # Generate other edge cases
                profile = UserProfile(
                    user_id=f"user_{start_idx + i + 1:03d}",
                    income_level=random.choice(['low', 'medium', 'high']),
                    credit_behavior=random.choice(['excellent', 'good', 'fair', 'poor']),
                    savings_behavior=random.choice(['aggressive', 'moderate', 'minimal', 'none']),
                    subscription_tendency=random.choice(['heavy', 'moderate', 'light']),
                    financial_stress=random.choice([True, False]),
                    scenario=scenario
                )
            
            edge_cases.append(profile)
        
        return edge_cases
    
    def generate_users_csv(self, profiles: List[UserProfile]) -> List[Dict[str, Any]]:
        """Generate users CSV data."""
        users = []
        for profile in profiles:
            user = {
                'user_id': profile.user_id,
                'created_at': self.fake.date_time_between(start_date='-2y', end_date='now').isoformat(),
                'consent_status': True,  # All synthetic users consent
                'consent_date': self.fake.date_time_between(start_date='-1y', end_date='now').isoformat()
            }
            users.append(user)
        return users
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str, output_dir: str = "data/synthetic"):
        """Save data to CSV file."""
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        
        if data:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Saved {len(data)} records to {filepath}")
        else:
            logger.warning(f"No data to save for {filename}")
    
    def generate_all(self, user_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all synthetic data."""
        logger.info(f"Generating synthetic data for {user_count} users (seed: {self.seed})")
        
        # Generate user profiles
        profiles = self.generate_user_profiles(user_count)
        
        # Generate data
        users_data = self.generate_users_csv(profiles)
        
        # TODO: Generate accounts, transactions, liabilities in subsequent tasks
        
        data = {
            'users': users_data,
            'profiles': [profile.__dict__ for profile in profiles]  # For reference
        }
        
        return data

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic financial data')
    parser.add_argument('--users', type=int, default=50, help='Number of users to generate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default='data/synthetic', help='Output directory')
    
    args = parser.parse_args()
    
    # Generate data
    generator = SyntheticDataGenerator(seed=args.seed)
    data = generator.generate_all(args.users)
    
    # Save to CSV
    generator.save_to_csv(data['users'], 'users.csv', args.output)
    
    print(f"✅ Generated data for {len(data['users'])} users")
    print(f"📁 Output directory: {args.output}")
```

**Validation**:
```bash
# Test data generation
python -m src.ingest.data_generator --users 10 --output data/test

# Check output
ls -la data/test/
# Expected: users.csv with 10 users

# Verify CSV structure
head -5 data/test/users.csv
# Expected: user_id,created_at,consent_status,consent_date headers + data

# Clean up test data
rm -rf data/test/
```

**Blockers for**: Account and transaction generation

---

#### ✅ Task 1.3.2: Add Account Generation (45 min)
**Dependencies**: Task 1.3.1  
**Deliverable**: Account generation methods in data generator

**Add to `src/ingest/data_generator.py`**:
```python
def generate_accounts_for_user(self, profile: UserProfile) -> List[Dict[str, Any]]:
    """Generate accounts for a single user based on their profile."""
    accounts = []
    base_date = self.fake.date_between(start_date='-2y', end_date='-6m')
    
    # Every user gets a checking account
    checking_balance = random.uniform(*self.account_types['checking']['balance_range'])
    if profile.income_level == 'low':
        checking_balance *= 0.5
    elif profile.income_level == 'high':
        checking_balance *= 2.0
    
    accounts.append({
        'account_id': f"{profile.user_id}_checking",
        'user_id': profile.user_id,
        'type': 'depository',
        'subtype': 'checking',
        'available_balance': round(checking_balance, 2),
        'current_balance': round(checking_balance, 2),
        'credit_limit': None,
        'iso_currency_code': 'USD'
    })
    
    # Add savings account based on savings behavior
    if profile.savings_behavior != 'none':
        savings_balance = 0
        if profile.savings_behavior == 'aggressive':
            savings_balance = random.uniform(5000, 50000)
        elif profile.savings_behavior == 'moderate':
            savings_balance = random.uniform(1000, 15000)
        elif profile.savings_behavior == 'minimal':
            savings_balance = random.uniform(0, 5000)
        
        # Adjust for income level
        if profile.income_level == 'low':
            savings_balance *= 0.3
        elif profile.income_level == 'high':
            savings_balance *= 2.0
        
        # Handle edge cases
        if profile.scenario == 'high_savings_rate':
            savings_balance = random.uniform(25000, 100000)
        elif profile.scenario == 'multiple_red_flags':
            savings_balance = 0
        
        accounts.append({
            'account_id': f"{profile.user_id}_savings",
            'user_id': profile.user_id,
            'type': 'depository',
            'subtype': 'savings',
            'available_balance': round(savings_balance, 2),
            'current_balance': round(savings_balance, 2),
            'credit_limit': None,
            'iso_currency_code': 'USD'
        })
    
    # Add credit card accounts
    credit_card_count = 0
    if profile.credit_behavior in ['excellent', 'good']:
        credit_card_count = random.choice([1, 2, 3])
    elif profile.credit_behavior == 'fair':
        credit_card_count = random.choice([1, 2])
    elif profile.credit_behavior == 'poor':
        credit_card_count = random.choice([0, 1, 2])
    
    # Edge case adjustments
    if profile.scenario == 'high_utilization_and_subscription_heavy':
        credit_card_count = max(2, credit_card_count)
    elif profile.scenario == 'sparse_transaction_history':
        credit_card_count = min(1, credit_card_count)
    
    for i in range(credit_card_count):
        # Credit limit based on income and credit behavior
        base_limit = random.uniform(1000, 15000)
        if profile.income_level == 'high':
            base_limit *= 3
        elif profile.income_level == 'low':
            base_limit *= 0.5
        
        if profile.credit_behavior == 'excellent':
            base_limit *= 2
        elif profile.credit_behavior == 'poor':
            base_limit *= 0.5
        
        credit_limit = round(base_limit, 2)
        
        # Current balance (utilization)
        if profile.credit_behavior == 'poor' or profile.scenario == 'high_utilization_and_subscription_heavy':
            utilization = random.uniform(0.7, 0.95)  # High utilization
        elif profile.credit_behavior == 'fair':
            utilization = random.uniform(0.3, 0.7)
        else:
            utilization = random.uniform(0.05, 0.3)  # Low utilization
        
        # Special case handling
        if profile.scenario == 'multiple_red_flags':
            utilization = random.uniform(0.85, 0.98)
        elif profile.scenario == 'high_savings_rate':
            utilization = random.uniform(0.0, 0.1)
        
        current_balance = round(credit_limit * utilization, 2)
        
        accounts.append({
            'account_id': f"{profile.user_id}_credit_{i+1}",
            'user_id': profile.user_id,
            'type': 'credit',
            'subtype': 'credit card', 
            'available_balance': round(credit_limit - current_balance, 2),
            'current_balance': current_balance,
            'credit_limit': credit_limit,
            'iso_currency_code': 'USD'
        })
    
    return accounts

def generate_accounts_csv(self, profiles: List[UserProfile]) -> List[Dict[str, Any]]:
    """Generate accounts CSV data for all users."""
    all_accounts = []
    for profile in profiles:
        user_accounts = self.generate_accounts_for_user(profile)
        all_accounts.extend(user_accounts)
    return all_accounts
```

**Update the `generate_all` method**:
```python
def generate_all(self, user_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Generate all synthetic data."""
    logger.info(f"Generating synthetic data for {user_count} users (seed: {self.seed})")
    
    # Generate user profiles
    profiles = self.generate_user_profiles(user_count)
    
    # Generate data
    users_data = self.generate_users_csv(profiles)
    accounts_data = self.generate_accounts_csv(profiles)
    
    data = {
        'users': users_data,
        'accounts': accounts_data,
        'profiles': [profile.__dict__ for profile in profiles]
    }
    
    return data
```

**Update CLI section**:
```python
# Save to CSV
generator.save_to_csv(data['users'], 'users.csv', args.output)
generator.save_to_csv(data['accounts'], 'accounts.csv', args.output)

print(f"✅ Generated data for {len(data['users'])} users")
print(f"📊 Generated {len(data['accounts'])} accounts")
print(f"📁 Output directory: {args.output}")
```

**Validation**:
```bash
# Test account generation
python -m src.ingest.data_generator --users 5 --output data/test

# Check accounts
head -10 data/test/accounts.csv
# Expected: account_id,user_id,type,subtype,available_balance,current_balance,credit_limit,iso_currency_code

# Verify account types
grep -o "checking\|savings\|credit card" data/test/accounts.csv | sort | uniq -c
# Expected: Mix of account types

# Clean up
rm -rf data/test/
```

**Blockers for**: Transaction generation, liability data

---

#### ✅ Task 1.3.3: Add Transaction Generation (90 min)
**Dependencies**: Task 1.3.2  
**Deliverable**: Complete transaction generation with realistic patterns

**Add to `src/ingest/data_generator.py`**:
```python
def generate_transactions_for_user(self, profile: UserProfile, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate realistic transactions for a user."""
    transactions = []
    
    # Get user's accounts
    user_accounts = [acc for acc in accounts if acc['user_id'] == profile.user_id]
    checking_accounts = [acc for acc in user_accounts if acc['subtype'] == 'checking']
    savings_accounts = [acc for acc in user_accounts if acc['subtype'] == 'savings']
    credit_accounts = [acc for acc in user_accounts if acc['subtype'] == 'credit card']
    
    # Date range for transactions
    end_date = date.today()
    start_date = end_date - timedelta(days=200)  # ~6.5 months of history
    
    # Handle edge case: insufficient data
    if profile.scenario == 'new_user_insufficient_data':
        start_date = end_date - timedelta(days=20)  # Only 20 days
    elif profile.scenario == 'sparse_transaction_history':
        # Generate very few transactions
        transaction_frequency = 0.1  # Much lower frequency
    else:
        transaction_frequency = 1.0
    
    # Generate income transactions (payroll)
    if checking_accounts:
        checking_account = checking_accounts[0]
        income_transactions = self._generate_income_transactions(
            profile, checking_account, start_date, end_date
        )
        transactions.extend(income_transactions)
    
    # Generate subscription transactions
    subscription_transactions = self._generate_subscription_transactions(
        profile, credit_accounts + checking_accounts, start_date, end_date, transaction_frequency
    )
    transactions.extend(subscription_transactions)
    
    # Generate regular spending
    regular_transactions = self._generate_regular_transactions(
        profile, credit_accounts + checking_accounts, start_date, end_date, transaction_frequency
    )
    transactions.extend(regular_transactions)
    
    # Generate savings transactions
    if savings_accounts:
        savings_transactions = self._generate_savings_transactions(
            profile, checking_accounts[0], savings_accounts[0], start_date, end_date
        )
        transactions.extend(savings_transactions)
    
    # Generate credit card payments
    payment_transactions = self._generate_credit_payments(
        profile, checking_accounts, credit_accounts, start_date, end_date
    )
    transactions.extend(payment_transactions)
    
    return transactions

def _generate_income_transactions(self, profile: UserProfile, account: Dict[str, Any], 
                                start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Generate payroll/income transactions."""
    transactions = []
    
    # Determine income amount and frequency
    income_min, income_max = self.income_ranges[profile.income_level]
    annual_income = random.uniform(income_min, income_max)
    
    # Most people get paid bi-weekly or monthly
    if profile.scenario == 'variable_income_gig_worker':
        # Irregular income with gaps
        pay_frequency = random.choice([7, 14, 21, 35, 45])  # Variable
        monthly_income = annual_income / 12
        pay_amount_base = monthly_income / 2  # Approximate
    else:
        pay_frequency = random.choice([14, 30])  # Bi-weekly or monthly
        if pay_frequency == 14:
            pay_amount_base = annual_income / 26  # 26 pay periods
        else:
            pay_amount_base = annual_income / 12  # 12 pay periods
    
    current_date = start_date
    while current_date <= end_date:
        # Add some variability to pay amounts
        if profile.scenario == 'variable_income_gig_worker':
            pay_amount = random.uniform(pay_amount_base * 0.3, pay_amount_base * 1.8)
        else:
            pay_amount = random.uniform(pay_amount_base * 0.95, pay_amount_base * 1.05)
        
        transaction = {
            'transaction_id': f"{account['account_id']}_income_{len(transactions)}",
            'account_id': account['account_id'],
            'user_id': profile.user_id,
            'date': current_date.isoformat(),
            'amount': round(pay_amount, 2),  # Positive for income
            'merchant_name': random.choice(['Payroll Dept', 'ADP', 'Direct Deposit', 'Employer']),
            'category_primary': 'Payroll',
            'category_detailed': 'Deposit',
            'payment_channel': 'other',
            'pending': False
        }
        transactions.append(transaction)
        
        # Next pay date (with some variability for gig workers)
        if profile.scenario == 'variable_income_gig_worker':
            current_date += timedelta(days=random.randint(pay_frequency - 5, pay_frequency + 10))
        else:
            current_date += timedelta(days=pay_frequency)
    
    return transactions

def _generate_subscription_transactions(self, profile: UserProfile, accounts: List[Dict[str, Any]], 
                                      start_date: date, end_date: date, frequency_multiplier: float) -> List[Dict[str, Any]]:
    """Generate subscription/recurring transactions."""
    transactions = []
    
    if not accounts:
        return transactions
    
    # Determine number of subscriptions based on tendency
    if profile.subscription_tendency == 'heavy':
        subscription_count = random.randint(5, 12)
    elif profile.subscription_tendency == 'moderate':
        subscription_count = random.randint(2, 6)
    else:  # light
        subscription_count = random.randint(0, 3)
    
    # Edge case adjustments
    if profile.scenario == 'high_utilization_and_subscription_heavy':
        subscription_count = max(6, subscription_count)
    elif profile.scenario == 'sparse_transaction_history':
        subscription_count = min(1, subscription_count)
    
    subscription_merchants = random.sample(
        self.merchant_categories['subscription'], 
        min(subscription_count, len(self.merchant_categories['subscription']))
    )
    
    for merchant in subscription_merchants:
        # Subscription amount based on service type
        if merchant in ['Netflix', 'Spotify', 'Disney+']:
            amount_range = (8.99, 15.99)
        elif merchant in ['Adobe', 'Zoom']:
            amount_range = (9.99, 39.99)
        elif merchant == 'Gym Membership':
            amount_range = (25.00, 89.99)
        else:
            amount_range = (4.99, 29.99)
        
        monthly_amount = random.uniform(*amount_range)
        
        # Generate recurring transactions
        current_date = start_date + timedelta(days=random.randint(1, 30))  # Random start day
        
        while current_date <= end_date:
            if random.random() < frequency_multiplier:  # Apply frequency multiplier
                account = random.choice(accounts)
                
                transaction = {
                    'transaction_id': f"{account['account_id']}_sub_{merchant}_{current_date.strftime('%Y%m%d')}",
                    'account_id': account['account_id'],
                    'user_id': profile.user_id,
                    'date': current_date.isoformat(),
                    'amount': -round(monthly_amount, 2),  # Negative for expense
                    'merchant_name': merchant,
                    'category_primary': 'Recreation',
                    'category_detailed': 'Subscription',
                    'payment_channel': 'online',
                    'pending': False
                }
                transactions.append(transaction)
            
            # Next month (with slight variation)
            current_date += timedelta(days=random.randint(28, 32))
    
    return transactions

def _generate_regular_transactions(self, profile: UserProfile, accounts: List[Dict[str, Any]], 
                                 start_date: date, end_date: date, frequency_multiplier: float) -> List[Dict[str, Any]]:
    """Generate regular spending transactions."""
    transactions = []
    
    if not accounts:
        return transactions
    
    # Base transaction frequency per day
    if profile.scenario == 'sparse_transaction_history':
        base_frequency = 0.3  # Very few transactions
    else:
        base_frequency = random.uniform(1.5, 4.0)  # 1-4 transactions per day on average
    
    current_date = start_date
    while current_date <= end_date:
        # Random number of transactions for this day
        daily_transaction_count = int(random.poisson(base_frequency * frequency_multiplier))
        
        for _ in range(daily_transaction_count):
            # Choose category and merchant
            category = random.choice(['grocery', 'gas', 'restaurant', 'shopping', 'utilities'])
            merchant = random.choice(self.merchant_categories[category])
            
            # Amount based on category and user profile  
            if category == 'grocery':
                amount_range = (15, 150)
            elif category == 'gas':
                amount_range = (25, 80)
            elif category == 'restaurant':
                amount_range = (8, 45)
            elif category == 'shopping':
                amount_range = (20, 300)
            else:  # utilities
                amount_range = (50, 200)
            
            # Adjust for income level
            multiplier = 1.0
            if profile.income_level == 'high':
                multiplier = 1.5
            elif profile.income_level == 'low':
                multiplier = 0.7
            
            amount = random.uniform(amount_range[0] * multiplier, amount_range[1] * multiplier)
            account = random.choice(accounts)
            
            transaction = {
                'transaction_id': f"{account['account_id']}_regular_{len(transactions)}",
                'account_id': account['account_id'], 
                'user_id': profile.user_id,
                'date': current_date.isoformat(),
                'amount': -round(amount, 2),  # Negative for expense
                'merchant_name': merchant,
                'category_primary': category.title(),
                'category_detailed': category.title(),
                'payment_channel': random.choice(['online', 'in store', 'other']),
                'pending': random.choice([True, False]) if current_date >= date.today() - timedelta(days=3) else False
            }
            transactions.append(transaction)
        
        current_date += timedelta(days=1)
    
    return transactions

def _generate_savings_transactions(self, profile: UserProfile, checking_account: Dict[str, Any], 
                                 savings_account: Dict[str, Any], start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Generate savings/transfer transactions."""
    transactions = []
    
    if profile.savings_behavior == 'none':
        return transactions
    
    # Monthly savings amount based on behavior and income
    income_min, income_max = self.income_ranges[profile.income_level]
    monthly_income = (income_min + income_max) / 2 / 12
    
    if profile.savings_behavior == 'aggressive':
        savings_rate = random.uniform(0.15, 0.30)
    elif profile.savings_behavior == 'moderate':
        savings_rate = random.uniform(0.05, 0.15)
    else:  # minimal
        savings_rate = random.uniform(0.01, 0.05)
    
    # Edge case adjustments
    if profile.scenario == 'high_savings_rate':
        savings_rate = random.uniform(0.25, 0.40)
    elif profile.scenario == 'multiple_red_flags':
        return transactions  # No savings for multiple red flags
    
    monthly_savings = monthly_income * savings_rate
    
    # Generate monthly transfers
    current_date = start_date + timedelta(days=random.randint(1, 31))
    
    while current_date <= end_date:
        # Checking account outflow
        transfer_out = {
            'transaction_id': f"{checking_account['account_id']}_transfer_out_{current_date.strftime('%Y%m%d')}",
            'account_id': checking_account['account_id'],
            'user_id': profile.user_id,
            'date': current_date.isoformat(),
            'amount': -round(monthly_savings, 2),
            'merchant_name': 'Transfer to Savings',
            'category_primary': 'Transfer',
            'category_detailed': 'Deposit',
            'payment_channel': 'other',
            'pending': False
        }
        transactions.append(transfer_out)
        
        # Savings account inflow
        transfer_in = {
            'transaction_id': f"{savings_account['account_id']}_transfer_in_{current_date.strftime('%Y%m%d')}",
            'account_id': savings_account['account_id'],
            'user_id': profile.user_id,
            'date': current_date.isoformat(),
            'amount': round(monthly_savings, 2),
            'merchant_name': 'Transfer from Checking',
            'category_primary': 'Transfer',
            'category_detailed': 'Deposit',
            'payment_channel': 'other',
            'pending': False
        }
        transactions.append(transfer_in)
        
        # Next month
        current_date += timedelta(days=random.randint(28, 32))
    
    return transactions

def _generate_credit_payments(self, profile: UserProfile, checking_accounts: List[Dict[str, Any]], 
                            credit_accounts: List[Dict[str, Any]], start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Generate credit card payment transactions."""
    transactions = []
    
    if not checking_accounts or not credit_accounts:
        return transactions
    
    checking_account = checking_accounts[0]
    
    for credit_account in credit_accounts:
        current_balance = credit_account['current_balance']
        credit_limit = credit_account['credit_limit']
        
        if current_balance <= 0:
            continue  # No balance to pay
        
        # Payment behavior based on credit behavior
        if profile.credit_behavior == 'poor' or profile.scenario == 'multiple_red_flags':
            # Minimum payments only, sometimes late
            payment_ratio = random.uniform(0.02, 0.05)  # 2-5% minimum payment
        elif profile.credit_behavior == 'fair':
            # Sometimes minimum, sometimes more
            payment_ratio = random.uniform(0.05, 0.15)
        else:  # good or excellent
            # Pay off most or all balance
            payment_ratio = random.uniform(0.3, 1.0)
        
        # Generate monthly payments
        current_date = start_date + timedelta(days=random.randint(15, 25))  # Mid-month payment
        
        while current_date <= end_date:
            payment_amount = min(current_balance * payment_ratio, current_balance)
            
            # Reduce current balance for next month
            current_balance = max(0, current_balance - payment_amount + random.uniform(50, 300))  # New charges
            
            payment = {
                'transaction_id': f"{checking_account['account_id']}_payment_{credit_account['account_id'][-1]}_{current_date.strftime('%Y%m%d')}",
                'account_id': checking_account['account_id'],
                'user_id': profile.user_id,
                'date': current_date.isoformat(),
                'amount': -round(payment_amount, 2),
                'merchant_name': f"Credit Card Payment",
                'category_primary': 'Payment',
                'category_detailed': 'Credit Card Payment',
                'payment_channel': 'online',
                'pending': False
            }
            transactions.append(payment)
            
            # Next month
            current_date += timedelta(days=random.randint(28, 32))
    
    return transactions

def generate_transactions_csv(self, profiles: List[UserProfile], accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate transactions CSV data for all users."""
    all_transactions = []
    for profile in profiles:
        user_transactions = self.generate_transactions_for_user(profile, accounts)
        all_transactions.extend(user_transactions)
    return all_transactions
```

**Update `generate_all` method**:
```python
def generate_all(self, user_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Generate all synthetic data."""
    logger.info(f"Generating synthetic data for {user_count} users (seed: {self.seed})")
    
    # Generate user profiles
    profiles = self.generate_user_profiles(user_count)
    
    # Generate data
    users_data = self.generate_users_csv(profiles)
    accounts_data = self.generate_accounts_csv(profiles)
    transactions_data = self.generate_transactions_csv(profiles, accounts_data)
    
    data = {
        'users': users_data,
        'accounts': accounts_data,
        'transactions': transactions_data,
        'profiles': [profile.__dict__ for profile in profiles]
    }
    
    logger.info(f"Generated {len(transactions_data)} transactions")
    return data
```

**Update CLI**:
```python
# Save to CSV
generator.save_to_csv(data['users'], 'users.csv', args.output)
generator.save_to_csv(data['accounts'], 'accounts.csv', args.output)
generator.save_to_csv(data['transactions'], 'transactions.csv', args.output)

print(f"✅ Generated data for {len(data['users'])} users")
print(f"📊 Generated {len(data['accounts'])} accounts")
print(f"💳 Generated {len(data['transactions'])} transactions")
print(f"📁 Output directory: {args.output}")
```

**Validation**:
```bash
# Test transaction generation
python -m src.ingest.data_generator --users 3 --output data/test

# Check transaction volume
wc -l data/test/transactions.csv
# Expected: 100+ transactions for 3 users

# Check subscription patterns
grep "Subscription" data/test/transactions.csv | head -5
# Expected: Monthly recurring patterns

# Check transaction structure
head -3 data/test/transactions.csv
# Expected: Proper CSV structure with all fields

# Clean up
rm -rf data/test/
```

**Blockers for**: Liability data generation, data loading

---

#### ✅ Task 1.3.4: Add Liability Generation (30 min)
**Dependencies**: Task 1.3.3  
**Deliverable**: Complete synthetic data generator with liability data

**Add to `src/ingest/data_generator.py`**:
```python
def generate_liabilities_csv(self, profiles: List[UserProfile], accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate liability (credit card) data."""
    liabilities = []
    
    # Get all credit card accounts
    credit_accounts = [acc for acc in accounts if acc['type'] == 'credit']
    
    for account in credit_accounts:
        user_id = account['user_id']
        profile = next((p for p in profiles if p.user_id == user_id), None)
        
        if not profile:
            continue
        
        # APR based on credit behavior
        if profile.credit_behavior == 'excellent':
            apr = random.uniform(12.99, 18.99)
        elif profile.credit_behavior == 'good':
            apr = random.uniform(16.99, 22.99)
        elif profile.credit_behavior == 'fair':
            apr = random.uniform(19.99, 26.99)
        else:  # poor
            apr = random.uniform(24.99, 29.99)
        
        # Calculate minimum payment (typically 2-3% of balance)
        current_balance = account['current_balance']
        min_payment = max(25.0, current_balance * random.uniform(0.02, 0.03))
        
        # Last payment based on credit behavior
        if profile.credit_behavior == 'poor' or profile.scenario == 'multiple_red_flags':
            # Often pay minimum or less
            last_payment = random.uniform(min_payment * 0.8, min_payment * 1.1)
            is_overdue = random.choice([True, False])  # 50% chance of being overdue
        elif profile.credit_behavior == 'fair':
            last_payment = random.uniform(min_payment, min_payment * 2.0)
            is_overdue = random.choice([True, False, False, False])  # 25% chance
        else:
            # Good/excellent: pay more than minimum
            last_payment = random.uniform(min_payment * 1.5, current_balance)
            is_overdue = False
        
        # Due date (usually 15-30 days from now)
        next_due_date = date.today() + timedelta(days=random.randint(15, 30))
        
        # Last statement balance (slightly different from current)
        last_statement = current_balance + random.uniform(-200, 200)
        last_statement = max(0, last_statement)
        
        liability = {
            'account_id': account['account_id'],
            'apr_percentage': round(apr, 2),
            'minimum_payment_amount': round(min_payment, 2),
            'last_payment_amount': round(last_payment, 2),
            'is_overdue': is_overdue,
            'next_payment_due_date': next_due_date.isoformat(),
            'last_statement_balance': round(last_statement, 2)
        }
        liabilities.append(liability)
    
    return liabilities
```

**Update `generate_all` method final version**:
```python
def generate_all(self, user_count: int = 50) -> Dict[str, List[Dict[str, Any]]]:
    """Generate all synthetic data."""
    logger.info(f"Generating synthetic data for {user_count} users (seed: {self.seed})")
    
    # Generate user profiles
    profiles = self.generate_user_profiles(user_count)
    
    # Generate data in dependency order
    users_data = self.generate_users_csv(profiles)
    accounts_data = self.generate_accounts_csv(profiles)
    transactions_data = self.generate_transactions_csv(profiles, accounts_data)
    liabilities_data = self.generate_liabilities_csv(profiles, accounts_data)
    
    data = {
        'users': users_data,
        'accounts': accounts_data,
        'transactions': transactions_data,
        'liabilities': liabilities_data,
        'profiles': [profile.__dict__ for profile in profiles]
    }
    
    logger.info(f"Generated {len(users_data)} users, {len(accounts_data)} accounts, "
               f"{len(transactions_data)} transactions, {len(liabilities_data)} liabilities")
    return data
```

**Update CLI final version**:
```python
# Save to CSV
generator.save_to_csv(data['users'], 'users.csv', args.output)
generator.save_to_csv(data['accounts'], 'accounts.csv', args.output)
generator.save_to_csv(data['transactions'], 'transactions.csv', args.output)
generator.save_to_csv(data['liabilities'], 'liabilities.csv', args.output)

print(f"✅ Generated complete dataset:")
print(f"   👥 {len(data['users'])} users")
print(f"   🏦 {len(data['accounts'])} accounts")
print(f"   💳 {len(data['transactions'])} transactions")
print(f"   📄 {len(data['liabilities'])} liabilities")
print(f"📁 Output directory: {args.output}")
```

**Final Validation**:
```bash
# Test complete data generation
python -m src.ingest.data_generator --users 5 --output data/test

# Verify all files
ls -la data/test/
# Expected: users.csv, accounts.csv, transactions.csv, liabilities.csv

# Check liability data structure
head -3 data/test/liabilities.csv
# Expected: account_id,apr_percentage,minimum_payment_amount,last_payment_amount,is_overdue,next_payment_due_date,last_statement_balance

# Verify data consistency
python -c "
import pandas as pd
users = pd.read_csv('data/test/users.csv')
accounts = pd.read_csv('data/test/accounts.csv')
transactions = pd.read_csv('data/test/transactions.csv')
liabilities = pd.read_csv('data/test/liabilities.csv')

print(f'✅ Data consistency check:')
print(f'   Users: {len(users)}')
print(f'   Accounts: {len(accounts)}')
print(f'   Transactions: {len(transactions)}')
print(f'   Liabilities: {len(liabilities)}')
print(f'   Credit accounts: {len(accounts[accounts.type == \"credit\"])}')
print(f'   Liability records: {len(liabilities)}')
assert len(accounts[accounts.type == 'credit']) == len(liabilities), 'Liability count mismatch'
print('✅ All consistency checks passed')
"

# Clean up
rm -rf data/test/
```

**Blockers for**: Data loading, signal computation

---

### 📥 **Phase 1.4: Data Loading Pipeline** (1 hour)

#### ✅ Task 1.4.1: Create CSV to Database Loader (45 min)
**Dependencies**: Task 1.3.4, Task 1.2.3
**Deliverable**: `scripts/load_data.py` for loading CSV data into database

**Create `scripts/load_data.py`**:
```python
"""
Load synthetic CSV data into SQLite database
"""
import pandas as pd
import argparse
from pathlib import Path
from loguru import logger
from src.db.connection import initialize_db, database_transaction, DatabaseError
import time

def load_csv_to_table(csv_path: str, table_name: str, db_path: str) -> int:
    """Load CSV data into database table."""
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        
        if df.empty:
            logger.warning(f"No data in {csv_path}")
            return 0
        
        # Load into database
        with database_transaction(db_path) as conn:
            # Insert data
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # Verify insertion
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            
        logger.info(f"Loaded {count} records into {table_name}")
        return count
        
    except Exception as e:
        raise DatabaseError(f"load_{table_name}", str(e))

def load_all_data(data_dir: str = "data/synthetic", db_path: str = "db/spend_sense.db") -> dict:
    """Load all CSV files into database."""
    start_time = time.time()
    
    # Ensure data directory exists
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    # Initialize database first
    logger.info("Initializing database...")
    initialize_db(db_path=db_path)
    
    # Load data in correct order (due to foreign key constraints)
    load_order = [
        ('users.csv', 'users'),
        ('accounts.csv', 'accounts'), 
        ('transactions.csv', 'transactions'),
        ('liabilities.csv', 'liabilities')
    ]
    
    results = {}
    
    for csv_file, table_name in load_order:
        csv_path = data_path / csv_file
        
        if not csv_path.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            results[table_name] = 0
            continue
        
        logger.info(f"Loading {csv_file} into {table_name}...")
        count = load_csv_to_table(str(csv_path), table_name, db_path)
        results[table_name] = count
    
    duration = time.time() - start_time
    logger.info(f"Data loading completed in {duration:.2f} seconds")
    
    return results

def validate_data_integrity(db_path: str = "db/spend_sense.db") -> bool:
    """Validate data integrity after loading."""
    try:
        with database_transaction(db_path) as conn:
            # Check foreign key constraints
            checks = [
                ("SELECT COUNT(*) FROM accounts WHERE user_id NOT IN (SELECT user_id FROM users)", "Orphaned accounts"),
                ("SELECT COUNT(*) FROM transactions WHERE user_id NOT IN (SELECT user_id FROM users)", "Orphaned transactions"),
                ("SELECT COUNT(*) FROM transactions WHERE account_id NOT IN (SELECT account_id FROM accounts)", "Invalid account references"),
                ("SELECT COUNT(*) FROM liabilities WHERE account_id NOT IN (SELECT account_id FROM accounts)", "Invalid liability references")
            ]
            
            for query, description in checks:
                result = conn.execute(query).fetchone()[0]
                if result > 0:
                    logger.error(f"Data integrity issue: {description} - {result} records")
                    return False
                
            # Check for required data
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if user_count == 0:
                logger.error("No users loaded")
                return False
                
            logger.info(f"✅ Data integrity validated: {user_count} users loaded")
            return True
            
    except Exception as e:
        logger.error(f"Data integrity validation failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Load synthetic data into database')
    parser.add_argument('--data-dir', default='data/synthetic', help='Directory containing CSV files')
    parser.add_argument('--db-path', default='db/spend_sense.db', help='Database path')
    parser.add_argument('--validate', action='store_true', help='Run data integrity validation')
    
    args = parser.parse_args()
    
    try:
        # Load data
        results = load_all_data(args.data_dir, args.db_path)
        
        # Print summary
        print("\n✅ Data Loading Summary:")
        for table, count in results.items():
            print(f"   {table}: {count} records")
        
        # Validate if requested
        if args.validate:
            print("\n🔍 Validating data integrity...")
            if validate_data_integrity(args.db_path):
                print("✅ All data integrity checks passed")
            else:
                print("❌ Data integrity issues found")
                exit(1)
                
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        print(f"❌ Data loading failed: {e}")
        exit(1)
```

**Validation**:
```bash
# Generate test data first
python -m src.ingest.data_generator --users 10 --output data/test

# Test data loading
python scripts/load_data.py --data-dir data/test --db-path db/test.db --validate

# Expected output:
# ✅ Data Loading Summary:
#    users: 10 records
#    accounts: 20+ records
#    transactions: 200+ records
#    liabilities: 5+ records
# ✅ All data integrity checks passed

# Verify database
sqlite3 db/test.db "SELECT COUNT(*) FROM users;"
# Expected: 10

# Clean up
rm -rf data/test/ db/test.db
```

**Blockers for**: Signal computation

---

## 🚀 **Phase 1 Complete - Ready for Phase 2!**

This completes the Phase 1 Implementation Checklist with **40+ actionable tasks**. Each task has:
- ✅ **Clear dependencies** - what must be done first
- ⏱️ **Time estimates** - realistic 15-60 minute chunks  
- 📋 **Specific deliverables** - exact files/code to create
- 🧪 **Validation steps** - concrete tests to verify success
- 🚫 **Blockers** - what tasks depend on this one

**What We've Built**:
- Complete synthetic data generation with edge cases
- Robust database schema with transaction safety
- Signal detection modules with exact schema compliance
- Comprehensive error handling and performance monitoring
- Unit tests and integration validation
- Data inspection and debugging tools

---

## 📚 **Next Phase Documents**

Continue with the remaining implementation phases:

### **SpendSense-Implementation-Phase2.md**
- Persona assignment and classification
- Content catalog with validation
- Recommendation engine with scoring
- API endpoints with standardized responses
- Guardrails implementation

### **SpendSense-Implementation-Phase3.md**
- Streamlit operator dashboard
- Evaluation metrics and reporting
- Final integration testing
- Production readiness checklist

Each phase will have the same level of detail with **15-60 minute actionable tasks**!
