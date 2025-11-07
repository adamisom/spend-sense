# Refactoring Opportunities - SpendSense

## 🎯 Overview

This document identifies key refactoring opportunities to improve code maintainability, reduce duplication, and enhance testability.

---

## 1. 🔧 Database Path Configuration (High Priority)

### Current State
- Hardcoded `"db/spend_sense.db"` appears in 9+ locations:
  - `src/db/connection.py` (multiple functions)
  - `src/ui/streamlit_app.py`
  - `src/evaluation/metrics.py`
  - `src/recommend/recommendation_engine.py`
  - `src/personas/persona_classifier.py`
  - `scripts/load_data.py`

### Problem
- Difficult to change database path
- Hard to test with different databases
- No environment-specific configuration
- Docker environment variable `DATABASE_PATH` is defined but not used

### Solution
Create `src/config/settings.py`:
```python
"""Application configuration."""
import os
from pathlib import Path
from typing import Optional

def get_database_path() -> str:
    """Get database path from environment or default."""
    return os.getenv("DATABASE_PATH", "db/spend_sense.db")

def get_schema_path() -> str:
    """Get schema path from environment or default."""
    return os.getenv("SCHEMA_PATH", "db/schema.sql")

def get_content_catalog_path() -> str:
    """Get content catalog path from environment or default."""
    return os.getenv("CONTENT_CATALOG_PATH", "data/content/catalog.json")
```

**Benefits**:
- Single source of truth for paths
- Environment variable support
- Easier testing with different paths
- Better Docker integration

**Files to Update**:
- All functions with `db_path: str = "db/spend_sense.db"` parameters
- Replace with `db_path: Optional[str] = None` and use `get_database_path()` as default

---

## 2. 📊 Signal JSON Parsing Utilities (High Priority)

### Current State
Signal JSON parsing and field extraction is duplicated:
- `src/ui/pages/user_analytics.py` (lines 43-59)
- `src/evaluation/metrics.py` (similar pattern in `_calculate_performance_metrics`)

### Problem
- Code duplication
- Inconsistent field extraction
- Hard to maintain if signal schema changes

### Solution
Create `src/features/signal_utils.py`:
```python
"""Utilities for working with user signals."""
import json
from typing import Dict, Any, Optional
import pandas as pd

from src.features.schema import UserSignals

def parse_signals_json(signals_json: str) -> Dict[str, Any]:
    """Parse signals JSON string to dictionary."""
    if not signals_json:
        return {}
    try:
        return json.loads(signals_json)
    except (json.JSONDecodeError, TypeError):
        return {}

def extract_signal_fields(df: pd.DataFrame, signals_column: str = 'signals') -> pd.DataFrame:
    """Extract common signal fields from DataFrame with signals JSON column."""
    if df.empty or signals_column not in df.columns:
        # Add empty columns for consistency
        df['data_quality_score'] = 0.0
        df['insufficient_data'] = True
        df['subscription_count'] = 0
        df['credit_utilization_max'] = None
        return df
    
    # Parse signals JSON
    df['parsed_signals'] = df[signals_column].apply(parse_signals_json)
    
    # Extract key signal metrics
    df['data_quality_score'] = df['parsed_signals'].apply(
        lambda x: x.get('data_quality_score', 0.0)
    )
    df['insufficient_data'] = df['parsed_signals'].apply(
        lambda x: x.get('insufficient_data', True)
    )
    df['subscription_count'] = df['parsed_signals'].apply(
        lambda x: x.get('subscription_count', 0)
    )
    df['credit_utilization_max'] = df['parsed_signals'].apply(
        lambda x: x.get('credit_utilization_max')
    )
    
    return df

def signals_dict_to_user_signals(signals_dict: Dict[str, Any]) -> Optional[UserSignals]:
    """Convert signals dictionary to UserSignals object."""
    try:
        return UserSignals(**signals_dict)
    except Exception:
        return None
```

**Benefits**:
- Single source of truth for signal parsing
- Consistent field extraction
- Easier to update when schema changes
- Reusable across dashboard and evaluation code

---

## 3. 🗄️ Database Query Repository Pattern (Medium Priority)

### Current State
Similar SQL queries duplicated across:
- `src/ui/streamlit_app.py` (system health queries)
- `src/ui/pages/user_analytics.py` (user data queries)
- `src/evaluation/metrics.py` (evaluation queries)

### Problem
- Query duplication
- Hard to maintain SQL
- Inconsistent query patterns
- No query optimization in one place

### Solution
Create `src/db/queries.py`:
```python
"""Common database queries for SpendSense."""
from typing import Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from src.db.connection import database_transaction

class SystemQueries:
    """System-level queries for dashboard."""
    
    @staticmethod
    def get_system_health(db_path: str) -> Dict[str, Any]:
        """Get basic system health metrics."""
        with database_transaction(db_path) as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            users_with_signals = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM user_signals"
            ).fetchone()[0]
            # ... rest of queries
            return {...}

class UserQueries:
    """User-related queries."""
    
    @staticmethod
    def get_users_with_signals(db_path: str, window: str = '180d') -> pd.DataFrame:
        """Get users with their signals and recommendations."""
        query = """
        SELECT 
            u.user_id,
            u.consent_status,
            s.window,
            s.signals,
            s.computed_at as signals_computed_at,
            COUNT(DISTINCT r.recommendation_id) as total_recommendations,
            MAX(r.created_at) as last_recommendation_at
        FROM users u
        LEFT JOIN user_signals s ON u.user_id = s.user_id AND s.window = ?
        LEFT JOIN recommendations r ON u.user_id = r.user_id
        GROUP BY u.user_id, u.consent_status, s.window, s.signals, s.computed_at
        ORDER BY u.user_id
        """
        with database_transaction(db_path) as conn:
            return pd.read_sql_query(query, conn, params=(window,))
```

**Benefits**:
- Centralized query management
- Easier to optimize queries
- Consistent query patterns
- Reusable across components

---

## 4. 📁 Directory Structure Cleanup (Low Priority)

### Current State
- Both `src/eval/` and `src/evaluation/` directories exist
- `src/eval/` appears to be empty/unused

### Solution
- Remove `src/eval/` if unused
- Consolidate to `src/evaluation/`

---

## 5. 🛡️ Error Handling Decorators (Medium Priority)

### Current State
Similar try/except patterns with logging repeated:
```python
try:
    # operation
except Exception as e:
    logger.error(f"Error: {e}")
    return default_value
```

### Solution
Create `src/utils/decorators.py`:
```python
"""Common decorators for error handling."""
from functools import wraps
from loguru import logger
from typing import Callable, Any, Optional

def handle_db_errors(default_return: Any = None):
    """Decorator to handle database errors consistently."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator
```

**Benefits**:
- Consistent error handling
- Less boilerplate
- Centralized error logging

---

## 6. 📈 Streamlit Dashboard Utilities (Medium Priority)

### Current State
System health queries in `streamlit_app.py` could be reused by other dashboard pages.

### Solution
Extract to `src/ui/utils/dashboard_queries.py`:
```python
"""Dashboard-specific database queries."""
from src.db.queries import SystemQueries

def get_system_health(db_path: str) -> dict:
    """Get system health for dashboard."""
    return SystemQueries.get_system_health(db_path)
```

**Benefits**:
- Reusable dashboard utilities
- Separation of concerns
- Easier to test

---

## 📋 Implementation Priority

1. **High Priority** (Do First):
   - Database path configuration (#1)
   - Signal JSON parsing utilities (#2)

2. **Medium Priority** (Do Next):
   - Database query repository (#3)
   - Error handling decorators (#5)
   - Dashboard utilities (#6)

3. **Low Priority** (Cleanup):
   - Directory structure (#4)

---

## 🧪 Testing Strategy

For each refactoring:
1. Write tests for new utility functions
2. Update existing code to use new utilities
3. Verify all tests still pass
4. Check for performance regressions

---

## 📝 Notes

- These refactorings are **non-breaking** - they improve internal structure without changing APIs
- Can be done incrementally
- Each refactoring can be done independently
- Consider doing during Phase 3 completion or as technical debt cleanup

