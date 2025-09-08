# Single Dockerfile for Render with proper routing
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY app.py .
COPY streamlit_app.py .
COPY streamlit_app2.py .
COPY .env* ./

# Create directories
RUN mkdir -p data prompts resume

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose only port 10000 (Render's default)
EXPOSE 10000

# Run the main router app
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"]
