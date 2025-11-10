# SpendSense - Optimized for Fast Development Iteration
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Development stage - optimized for fast rebuilds
FROM base as development

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies (cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p db data/synthetic logs

# Set Python path for development
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000 8501

# Keep container running for development (overridden by docker-compose)
CMD ["tail", "-f", "/dev/null"]

# Production stage (for future use)
FROM development as production

# Copy source code (only in production to avoid rebuild on every change)
COPY . .

# Production command - Streamlit for Railway deployment
CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true"]
