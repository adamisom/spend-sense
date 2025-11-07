#!/usr/bin/env python3
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

