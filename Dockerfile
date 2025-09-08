# Single Dockerfile for both Streamlit apps
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY streamlit_app.py ./apps/
COPY streamlit_app2.py ./apps/
COPY main_app.py .
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY .env* ./

# Create necessary directories
RUN mkdir -p data prompts resume logs

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8501
EXPOSE 8502

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8503/health || exit 1

# Start supervisor to manage multiple processes
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
