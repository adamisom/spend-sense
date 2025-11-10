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
    
    # Ensure connection is closed if we somehow exit the loop without success
    if conn:
        conn.close()

def run_demographic_migration(db_path: str = "db/spend_sense.db"):
    """Run migration to add demographic columns to users table if they don't exist."""
    try:
        with database_transaction(db_path) as conn:
            # Check if demographic columns exist
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            migrations_needed = []
            if 'age' not in columns:
                migrations_needed.append("ALTER TABLE users ADD COLUMN age INTEGER")
            if 'age_range' not in columns:
                migrations_needed.append("ALTER TABLE users ADD COLUMN age_range TEXT")
            if 'gender' not in columns:
                migrations_needed.append("ALTER TABLE users ADD COLUMN gender TEXT")
            if 'race_ethnicity' not in columns:
                migrations_needed.append("ALTER TABLE users ADD COLUMN race_ethnicity TEXT")
            if 'demographic_group' not in columns:
                migrations_needed.append("ALTER TABLE users ADD COLUMN demographic_group TEXT")
            
            # Run migrations
            for migration in migrations_needed:
                conn.execute(migration)
                logger.info(f"Applied migration: {migration}")
            
            # Check if index exists
            indexes = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_users_demographic_group'
            """).fetchone()
            
            if not indexes:
                conn.execute("CREATE INDEX idx_users_demographic_group ON users(demographic_group)")
                logger.info("Created index: idx_users_demographic_group")
            
            if migrations_needed:
                logger.info("Demographic migration completed successfully")
            else:
                logger.debug("Demographic columns already exist, no migration needed")
                
    except Exception as e:
        logger.warning(f"Demographic migration failed (may already be applied): {e}")

def initialize_db(schema_path: str = "db/schema.sql", db_path: str = "db/spend_sense.db", force: bool = False):
    """Initialize database from schema file.
    
    Args:
        schema_path: Path to schema SQL file
        db_path: Path to database file
        force: If True, drop existing tables and recreate. If False, skip if tables exist.
    """
    try:
        if not Path(schema_path).exists():
            raise DatabaseError("initialization", f"Schema file not found: {schema_path}")
        
        with database_transaction(db_path) as conn:
            # Check if database is already initialized
            if not force:
                try:
                    result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
                    if result:
                        logger.info(f"Database already initialized: {db_path} (use force=True to reinitialize)")
                        # Run demographic migration for existing databases
                        run_demographic_migration(db_path)
                        return
                except sqlite3.Error:
                    pass  # Table doesn't exist, proceed with initialization
            
            # If force=True, drop existing tables
            if force:
                logger.info("Dropping existing tables...")
                conn.execute("DROP TABLE IF EXISTS recommendations")
                conn.execute("DROP TABLE IF EXISTS persona_assignments")
                conn.execute("DROP TABLE IF EXISTS user_signals")
                conn.execute("DROP TABLE IF EXISTS liabilities")
                conn.execute("DROP TABLE IF EXISTS transactions")
                conn.execute("DROP TABLE IF EXISTS accounts")
                conn.execute("DROP TABLE IF EXISTS users")
            
            # Create tables from schema
            with open(schema_path) as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
        
        logger.info(f"Database initialized successfully: {db_path}")
        
    except Exception as e:
        raise DatabaseError("initialization", str(e))

def save_user_signals(user_id: str, window: str, signals: Dict[str, Any], db_path: str = "db/spend_sense.db"):
    """Save computed signals to database."""
    try:
        # Handle datetime serialization
        def json_serializer(obj):
            """JSON serializer for objects not serializable by default json code"""
            from datetime import datetime
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        # Serialize signals with datetime handling
        signals_json = json.dumps(signals, default=json_serializer)
        
        with database_transaction(db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_signals (user_id, window, signals)
                VALUES (?, ?, ?)
            """, (user_id, window, signals_json))
        
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


