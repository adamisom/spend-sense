#!/bin/bash
# Railway startup script - handles PORT variable expansion

set -e

# Railway sets PORT=8080 but routes to 8000, so we force 8000
PORT=8000

echo "🚀 Starting Streamlit on port $PORT (Railway routes to 8000)"

# Run Streamlit with expanded PORT variable
exec streamlit run src/ui/streamlit_app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true

