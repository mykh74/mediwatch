# MediWatch API Docker Image
FROM python:3.11-slim

LABEL maintainer="MediWatch Team"
LABEL description="Patient Readmission Prediction API"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY api /app/api
COPY scripts /opt/scripts
COPY pyproject.toml /app/pyproject.toml

# Install the package in editable mode for simple imports
RUN pip install --no-cache-dir -e .

# Create directories for models and data
# Models and preprocessing artifacts will be fetched from MLflow at runtime
RUN mkdir -p /app/models /app/data/processed

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
