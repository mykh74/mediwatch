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
COPY pyproject.toml /app/pyproject.toml
COPY models /app/models
COPY data/processed/preprocessing_artifacts.pkl /app/data/processed/preprocessing_artifacts.pkl

# Install the package in editable mode for simple imports
RUN pip install --no-cache-dir -e .

# Create data directory for preprocessing artifacts
RUN mkdir -p /app/data/processed

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
