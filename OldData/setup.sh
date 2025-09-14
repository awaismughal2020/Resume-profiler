#!/bin/bash

# Setup script for Resume AI Platform (HTML/CSS/JS version)

# Create necessary directories
echo "Creating directory structure..."
mkdir -p css js images data prompts resume logs

# Create Dockerfiles if they don't exist
echo "Creating Dockerfiles..."

# Create Dockerfile.streamlit1 if it doesn't exist
if [ ! -f "Dockerfile.streamlit1" ]; then
  cat > Dockerfile.streamlit1 << 'EOF'
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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY streamlit_app.py .
COPY pdf_reader.py .
COPY cv_analyzer.py .
COPY prompts/ ./prompts/

# Create necessary directories
RUN mkdir -p data prompts resume

# Expose port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
EOF
fi

# Create Dockerfile.streamlit2 if it doesn't exist
if [ ! -f "Dockerfile.streamlit2" ]; then
  cat > Dockerfile.streamlit2 << 'EOF'
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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY streamlit_app2.py .
COPY prompts/ ./prompts/

# Create necessary directories
RUN mkdir -p data prompts

# Expose port
EXPOSE 8502

# Command to run the application
CMD ["streamlit", "run", "streamlit_app2.py", "--server.port=8502", "--server.address=0.0.0.0", "--server.headless=true"]
EOF
fi

# Create nginx.conf if it doesn't exist
if [ ! -f "nginx.conf" ]; then
  cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/javascript;

    # Handle SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Legacy streamlit apps (optional)
    location /cv-analyzer/ {
        proxy_pass http://cv-analyzer:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /cv-enhancement/ {
        proxy_pass http://cv-enhancement:8502/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Cache static assets
    location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Health check endpoint
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF
fi

echo "Setup complete! Directory structure created."
echo "Now you can copy the HTML, CSS, and JS files to their respective directories."
echo "Use the following command to deploy the application:"
echo "docker-compose up -d"
