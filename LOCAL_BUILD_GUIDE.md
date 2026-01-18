# MediWatch Local Build and Test Guide

Complete guide for building and testing the entire MediWatch project locally on your Mac.

## 🎯 Quick Start (5 Minutes)

```bash
# 1. Start Docker Desktop (from Applications)
# 2. Run the complete setup
cd /Users/michaelkuzmyn/projects/ik/MediWatch
./scripts/local_setup.sh
```

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step-by-Step Setup](#step-by-step-setup)
3. [Component Testing](#component-testing)
4. [Full Integration Test](#full-integration-test)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Tool | Version | Purpose | Installation |
|------|---------|---------|--------------|
| **Docker Desktop** | Latest | Container platform | [Download](https://www.docker.com/products/docker-desktop) |
| **Python** | 3.11+ | Runtime | `brew install python@3.11` |
| **Git** | Latest | Version control | Pre-installed on Mac |

### Optional (For Full Testing)

| Tool | Purpose | Installation |
|------|---------|--------------|
| **Minikube** | Local Kubernetes | `brew install minikube` |
| **kubectl** | Kubernetes CLI | `brew install kubectl` |
| **Apache Airflow** | Orchestration (if testing DAGs) | Included in setup |

---

## Step-by-Step Setup

### Phase 1: Environment Setup (5 minutes)

#### 1.1 Start Docker Desktop

```bash
# Open Docker Desktop application
open -a Docker

# Wait for Docker to start (watch for whale icon in menu bar)
# Verify Docker is running
docker info
```

**Expected Output:**
```
Server:
 Containers: 0
  Running: 0
...
```

#### 1.2 Clone/Navigate to Project

```bash
cd /Users/michaelkuzmyn/projects/ik/MediWatch
```

#### 1.3 Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### 1.4 Install Python Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install project in editable mode
pip install -e .

# Install additional tools for testing
pip install pytest requests apache-airflow==2.8.0
```

**Expected Time:** 3-5 minutes

---

### Phase 2: Data and Model Setup (10 minutes)

#### 2.1 Verify Data Files

```bash
# Check if raw data exists
ls -lh data/raw/diabetic_data.csv

# Check if processed data exists
ls -lh data/processed/train.csv
ls -lh data/processed/test.csv
```

**If data is missing:**
```bash
# Download and preprocess data
python scripts/download_data.py
python scripts/preprocess_data.py
```

#### 2.2 Start MLflow Server

```bash
# Terminal 1: Start MLflow in background
python scripts/setup_mlflow.py --action start

# Or manually
nohup .venv/bin/mlflow server \
  --host 127.0.0.1 \
  --port 5000 \
  --backend-store-uri sqlite:///mlruns.db \
  --default-artifact-root ./mlruns > mlflow.log 2>&1 &

# Verify MLflow is running
curl http://localhost:5000/health
```

**Expected Output:**
```json
{"status": "ok"}
```

**Access MLflow UI:** http://localhost:5000

#### 2.3 Train Models (Optional - if no models exist)

```bash
# Check if models exist in MLflow
ls -la mlruns/1/models/

# If needed, train models
python scripts/train_models.py
```

**Expected Time:** 5-15 minutes depending on data size

#### 2.4 Register Best Model

```bash
# Interactive Jupyter notebook for model selection
jupyter notebook notebooks/02_model_training.ipynb
```

Or programmatically:
```python
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

# Find best model and register
# (This is typically done in the notebook)
```

---

### Phase 3: API Testing (5 minutes)

#### 3.1 Set Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
MODEL_NAME=mediwatch_readmission_classifier
MODEL_STAGE=Production
PREPROCESSING_ARTIFACTS_PATH=data/processed/preprocessing_artifacts.pkl
EOF

# Load environment
export $(cat .env | xargs)
```

#### 3.2 Start FastAPI Server

```bash
# Terminal 2: Start API server
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python api/main.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Access API Documentation:** http://localhost:8000/docs

#### 3.3 Test API Endpoints

```bash
# Terminal 3: Test health endpoint
curl http://localhost:8000/health

# Test model info
curl http://localhost:8000/model/info

# Test prediction (use the provided test script)
python test_api.py
```

**Expected Output:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "mlflow_connected": true
}
```

---

### Phase 4: Docker Build (10 minutes)

#### 4.1 Build API Docker Image

```bash
# Build image
docker build -t mediwatch-api:latest -f api/Dockerfile .

# Verify image
docker images | grep mediwatch
```

**Expected Output:**
```
mediwatch-api   latest   abc123def456   2 minutes ago   850MB
```

#### 4.2 Test Docker Container

```bash
# Run container (make sure MLflow is still running on host)
docker run -d \
  --name mediwatch-api-test \
  -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=mediwatch_readmission_classifier \
  -e MODEL_STAGE=Production \
  mediwatch-api:latest

# Check logs
docker logs mediwatch-api-test

# Test API
curl http://localhost:8000/health

# Cleanup
docker stop mediwatch-api-test
docker rm mediwatch-api-test
```

---

### Phase 5: Jenkins CI/CD (15 minutes)

#### 5.1 Start Jenkins with Docker Compose

```bash
# Navigate to CI/CD directory
cd ci-cd

# Start Jenkins
./scripts/start_jenkins.sh

# Or manually
docker-compose -f docker-compose.jenkins.yml up -d

# Wait for Jenkins to start (30-60 seconds)
docker-compose -f docker-compose.jenkins.yml logs -f jenkins
```

**Access Jenkins:** http://localhost:8080

#### 5.2 Initial Jenkins Setup

```bash
# Get initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

1. Navigate to http://localhost:8080
2. Enter the initial admin password
3. Click "Install suggested plugins"
4. Create admin user:
   - Username: `admin`
   - Password: `admin123` (or your choice)
   - Email: your-email@example.com

#### 5.3 Configure Jenkins Job

**See [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md) for detailed configuration steps.**

Quick setup:
1. New Item → Pipeline → Name: `mediwatch-ci-cd`
2. Pipeline Definition: "Pipeline script from SCM"
3. SCM: Git
4. Repository URL: `/workspace` (mounted in container)
5. Branch: `*/main` or `*/master`
6. Script Path: `Jenkinsfile`
7. Save

#### 5.4 Test Jenkins Build

```bash
# Trigger build from CLI
cd /Users/michaelkuzmyn/projects/ik/MediWatch
python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --deploy-mode docker \
  --run-tests true

# Or manually in Jenkins UI
# Click "Build with Parameters" and select options
```

---

### Phase 6: Airflow Orchestration (Optional, 20 minutes)

#### 6.1 Install Airflow

```bash
# Airflow requires specific installation
pip install apache-airflow==2.8.0 \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.0/constraints-3.11.txt"
```

#### 6.2 Initialize Airflow

```bash
# Set Airflow home
export AIRFLOW_HOME=~/airflow

# Initialize database
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin
```

#### 6.3 Configure DAGs

```bash
# Link DAG directory
mkdir -p ~/airflow/dags
ln -s /Users/michaelkuzmyn/projects/ik/MediWatch/orchestration/airflow/dags/* ~/airflow/dags/

# Or copy DAGs
cp orchestration/airflow/dags/*.py ~/airflow/dags/
```

#### 6.4 Start Airflow

```bash
# Terminal 4: Start webserver
airflow webserver --port 8081

# Terminal 5: Start scheduler
airflow scheduler
```

**Access Airflow UI:** http://localhost:8081

---

## Component Testing

### Test 1: Python Environment ✓

```bash
# Verify Python version
python --version  # Should be 3.11+

# Verify packages
pip list | grep -E "mlflow|fastapi|scikit-learn|xgboost"

# Run package test
python -c "import mlflow, fastapi, sklearn, xgboost; print('✓ All packages imported')"
```

### Test 2: MLflow ✓

```bash
# Test MLflow connection
python << EOF
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
print(f"✓ MLflow tracking URI: {mlflow.get_tracking_uri()}")
print(f"✓ Experiments: {[e.name for e in mlflow.search_experiments()]}")
EOF
```

### Test 3: Data Pipeline ✓

```bash
# Test preprocessing
python << EOF
from src.mediwatch.data.preprocess import load_and_preprocess
df = load_and_preprocess("data/processed/train.csv")
print(f"✓ Loaded {len(df)} rows")
EOF
```

### Test 4: Model Loading ✓

```bash
# Test model registry
python << EOF
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")

try:
    model_uri = "models:/mediwatch_readmission_classifier/Production"
    model = mlflow.pyfunc.load_model(model_uri)
    print(f"✓ Model loaded from: {model_uri}")
except Exception as e:
    print(f"✗ Model loading failed: {e}")
EOF
```

### Test 5: API Health ✓

```bash
# Test all API endpoints
python << EOF
import requests
base_url = "http://localhost:8000"

endpoints = ["/", "/health", "/model/info"]
for endpoint in endpoints:
    response = requests.get(f"{base_url}{endpoint}")
    status = "✓" if response.status_code == 200 else "✗"
    print(f"{status} {endpoint}: {response.status_code}")
EOF
```

### Test 6: Docker ✓

```bash
# Run comprehensive Docker test
./ci-cd/scripts/test_setup.sh
```

### Test 7: Jenkins Pipeline ✓

```bash
# Trigger and monitor Jenkins build
python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --deploy-mode docker \
  --wait
```

---

## Full Integration Test

### Complete End-to-End Workflow

```bash
#!/bin/bash
# Full integration test script

set -e

echo "🚀 MediWatch Full Integration Test"
echo "=================================="

# 1. Start services
echo "📦 Starting services..."
docker-compose -f ci-cd/docker-compose.jenkins.yml up -d
sleep 10

# 2. Start MLflow
echo "🔬 Starting MLflow..."
python scripts/setup_mlflow.py --action start
sleep 5

# 3. Test API
echo "🌐 Testing API..."
python test_api.py

# 4. Build Docker image
echo "🐳 Building Docker image..."
docker build -t mediwatch-api:test -f api/Dockerfile .

# 5. Test Docker deployment
echo "🚢 Testing Docker deployment..."
docker run -d --name mediwatch-test \
  -p 8001:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  mediwatch-api:test

sleep 10
curl http://localhost:8001/health

# 6. Cleanup
echo "🧹 Cleaning up..."
docker stop mediwatch-test
docker rm mediwatch-test

echo "✅ Integration test complete!"
```

---

## Troubleshooting

### Issue: Docker Not Running

**Symptom:** `Cannot connect to the Docker daemon`

**Solution:**
```bash
# Start Docker Desktop
open -a Docker

# Wait 30 seconds, then verify
docker info
```

### Issue: Port Already in Use

**Symptom:** `Port 8000 is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

### Issue: MLflow Connection Failed

**Symptom:** `Connection refused to localhost:5000`

**Solution:**
```bash
# Check if MLflow is running
ps aux | grep mlflow

# Restart MLflow
pkill -f mlflow
python scripts/setup_mlflow.py --action start

# Verify
curl http://localhost:5000/health
```

### Issue: Model Not Found

**Symptom:** `Model 'mediwatch_readmission_classifier' not found`

**Solution:**
```bash
# List available models
python << EOF
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
from mlflow.tracking import MlflowClient
client = MlflowClient()
models = client.search_registered_models()
for model in models:
    print(f"Model: {model.name}")
EOF

# Train and register model
python scripts/train_models.py
jupyter notebook notebooks/02_model_training.ipynb
```

### Issue: Jenkins Build Fails

**Symptom:** Build fails in Jenkins

**Solution:**
```bash
# Check Jenkins logs
docker logs jenkins

# Verify Jenkins can access Docker
docker exec jenkins docker ps

# Check workspace permissions
docker exec jenkins ls -la /workspace
```

### Issue: Virtual Environment Issues

**Symptom:** Package import errors

**Solution:**
```bash
# Recreate virtual environment
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## 📊 Success Criteria

Your local build is successful when:

- [ ] Docker Desktop is running
- [ ] Python virtual environment is activated
- [ ] All Python packages installed (52+ packages)
- [ ] MLflow server accessible at http://localhost:5000
- [ ] Models registered in MLflow registry
- [ ] FastAPI serving at http://localhost:8000
- [ ] API health check returns `200 OK`
- [ ] Docker image builds successfully
- [ ] Jenkins accessible at http://localhost:8080
- [ ] Jenkins pipeline runs successfully
- [ ] Docker container serves API correctly

---

## 🎯 Quick Commands Reference

```bash
# Environment
source .venv/bin/activate
export $(cat .env | xargs)

# Services
python scripts/setup_mlflow.py --action start
uvicorn api.main:app --reload --port 8000
cd ci-cd && ./scripts/start_jenkins.sh

# Testing
python test_api.py
./ci-cd/scripts/test_setup.sh
curl http://localhost:8000/health

# Docker
docker build -t mediwatch-api:latest -f api/Dockerfile .
docker-compose -f ci-cd/docker-compose.jenkins.yml up -d
docker-compose -f ci-cd/docker-compose.jenkins.yml logs -f

# Cleanup
docker-compose -f ci-cd/docker-compose.jenkins.yml down
pkill -f mlflow
deactivate
```

---

## Next Steps

1. **Testing**: Run through all test phases
2. **CI/CD**: Configure Jenkins job and test pipeline
3. **Monitoring**: Set up Evidently for drift detection
4. **Production**: Deploy to cloud (GCP, AWS, Azure)
5. **Kubernetes**: Test K8s deployment with minikube

---

## Resources

- **API Documentation**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000
- **Jenkins UI**: http://localhost:8080
- **Airflow UI**: http://localhost:8081 (if installed)

- **Setup Guide**: [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md)
- **Deployment Guide**: [docs/deployment.md](docs/deployment.md)
- **Quick Start**: [docs/quick_start.md](docs/quick_start.md)

---

**Last Updated:** January 17, 2026  
**Project:** MediWatch v1.0  
**Author:** MediWatch Team
