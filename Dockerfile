# Stage 1: Build & Runtime using Python slim base for reduced attack surface and minimal image size
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_APP=app.py

WORKDIR /app

# Install build/security tools and clean up apt cache to optimize image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies in a separate layer for Docker build caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and test suite
COPY . .

# Create a non-privileged user and group for container security
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin -c "Docker App User" appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose standard application port
EXPOSE 5000

# Health check probe for container orchestration & health monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch application
CMD ["python", "app.py"]
