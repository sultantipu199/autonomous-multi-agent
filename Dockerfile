# ==============================================================================
# Production Dockerfile for Autonomous Multi-Agent Growth Platform (24/7 Cloud)
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Set non-interactive and unbuffered environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install system dependencies for Pillow, PyMuPDF, and font rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure data directory exists
RUN mkdir -p data output

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Launch 24/7 autonomous bot supervisor
CMD ["python", "main.py"]
