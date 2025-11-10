#!/bin/bash
# Railway initialization script - runs on container startup
# Checks if database is initialized and sets it up if needed

set -e

DB_PATH="${DATABASE_PATH:-/app/db/spend_sense.db}"
INIT_FLAG="/app/db/.initialized"

echo "🚀 Railway initialization script starting..."

# Check if already initialized
if [ -f "$INIT_FLAG" ]; then
    echo "✅ Database already initialized, skipping setup"
    exit 0
fi

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "📦 Initializing database..."
    python3 -c "from src.db.connection import initialize_db; initialize_db()"
    
    echo "👥 Generating synthetic users..."
    python3 -m src.ingest.data_generator --users 50
    
    echo "📥 Loading data..."
    python3 scripts/load_data.py
    
    echo "🔧 Computing signals..."
    python3 scripts/compute_signals.py
    
    echo "💡 Generating recommendations..."
    python3 scripts/generate_recommendations.py --all
    
    # Mark as initialized
    touch "$INIT_FLAG"
    echo "✅ Initialization complete!"
else
    echo "📊 Database exists, checking if data is loaded..."
    
    # Check if users table has data
    USER_COUNT=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    conn.close()
    print(count)
except:
    print(0)
")
    
    if [ "$USER_COUNT" -eq "0" ]; then
        echo "📥 Database empty, loading data..."
        python3 -m src.ingest.data_generator --users 50
        python3 scripts/load_data.py
        python3 scripts/compute_signals.py
        python3 scripts/generate_recommendations.py --all
        touch "$INIT_FLAG"
        echo "✅ Data loaded!"
    else
        # Check if signals exist
        SIGNAL_COUNT=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    count = conn.execute(\"SELECT COUNT(*) FROM user_signals WHERE window = '180d'\").fetchone()[0]
    conn.close()
    print(count)
except:
    print(0)
")
        
        if [ "$SIGNAL_COUNT" -eq "0" ]; then
            echo "🔧 Users exist but no signals found, computing signals..."
            python3 scripts/compute_signals.py
            python3 scripts/generate_recommendations.py --all
            touch "$INIT_FLAG"
            echo "✅ Signals computed!"
        else
            echo "✅ Database already has data ($USER_COUNT users, $SIGNAL_COUNT signals)"
            touch "$INIT_FLAG"
        fi
    fi
fi

