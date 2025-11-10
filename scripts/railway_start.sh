#!/bin/bash
# Railway startup script - handles PORT variable expansion

set -e

# Get PORT from environment (Railway sets this)
PORT=${PORT:-8080}

echo "🚀 Starting Streamlit on port $PORT"

# Run Streamlit with expanded PORT variable
exec streamlit run src/ui/streamlit_app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true

