#!/bin/bash
# Quick diagnostic script to check if data persists in Railway

DB_PATH="${DATABASE_PATH:-/app/db/spend_sense.db}"
INIT_FLAG="/app/db/.initialized"

echo "🔍 Railway Persistence Diagnostic"
echo "=================================="
echo ""

# Check if database file exists
if [ -f "$DB_PATH" ]; then
    echo "✅ Database file exists: $DB_PATH"
    FILE_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null || echo "unknown")
    echo "   Size: $FILE_SIZE bytes"
else
    echo "❌ Database file NOT found: $DB_PATH"
fi

echo ""

# Check if init flag exists
if [ -f "$INIT_FLAG" ]; then
    echo "✅ Init flag exists: $INIT_FLAG"
    FLAG_AGE=$(stat -f%Sm -t "%Y-%m-%d %H:%M:%S" "$INIT_FLAG" 2>/dev/null || stat -c%y "$INIT_FLAG" 2>/dev/null || echo "unknown")
    echo "   Created: $FLAG_AGE"
else
    echo "❌ Init flag NOT found: $INIT_FLAG"
fi

echo ""

# Check database contents
if [ -f "$DB_PATH" ]; then
    echo "📊 Database Contents:"
    python3 << EOF
import sqlite3
try:
    conn = sqlite3.connect('$DB_PATH')
    
    # Count users
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    print(f"   Users: {user_count}")
    
    # Count transactions
    txn_count = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
    print(f"   Transactions: {txn_count}")
    
    # Count signals
    signal_count = conn.execute("SELECT COUNT(*) FROM user_signals WHERE window = '180d'").fetchone()[0]
    print(f"   Signals (180d): {signal_count}")
    
    # Sample data quality
    if signal_count > 0:
        quality_result = conn.execute("""
            SELECT AVG(CAST(JSON_EXTRACT(signals, '$.data_quality_score') AS FLOAT))
            FROM user_signals WHERE window = '180d'
        """).fetchone()[0]
        quality = quality_result if quality_result else 0.0
        print(f"   Avg Data Quality: {quality:.2f}")
    
    conn.close()
except Exception as e:
    print(f"   Error reading database: {e}")
EOF
else
    echo "❌ Cannot check contents - database file doesn't exist"
fi

echo ""
echo "💡 If you see 'Initializing database...' in logs on every deploy,"
echo "   data is NOT persisting. You need to add a Railway volume."

