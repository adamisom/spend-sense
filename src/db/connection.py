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

