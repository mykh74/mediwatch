# MediWatch Quick Test Guide

Fast guide to test the complete deployment cycle locally.

## 🚀 One-Command Test

```bash
# Make sure Docker Desktop is running, then:
./scripts/test_full_deployment.sh
```

This script tests the **entire deployment cycle**:
- ✅ Data pipeline (download → preprocess)
- ✅ MLflow setup & model registry
- ✅ Model training (if needed)
- ✅ FastAPI server
- ✅ Predictions & API endpoints
- ✅ Docker image build
- ✅ Container deployment
- ✅ Jenkins CI/CD setup

**Time:** 15-30 minutes (first run with training), 5-10 minutes (subsequent runs)

---

## 📋 What It Does

### Phase 1: Prerequisites ✓
- Checks Docker is running
- Verifies Python environment
- Validates dependencies

### Phase 2: Data Pipeline ✓
- Downloads raw data (if missing)
- Preprocesses data
- Validates data splits

### Phase 3: MLflow & Models ✓
- Starts MLflow server
- Checks for existing models
- Connects to model registry

### Phase 4: Model Training ✓
- Trains 6 ML algorithms (if needed)
- Logs experiments to MLflow
- Registers best model as Production

### Phase 5: API Testing ✓
- Starts FastAPI server
- Tests health endpoint
- Tests prediction endpoint
- Validates responses

### Phase 6: Docker Deployment ✓
- Builds Docker image
- Runs container
- Tests containerized API
- Validates predictions

### Phase 7: Jenkins CI/CD ✓
- Starts Jenkins container
- Validates Jenkinsfile
- Displays initial password
- Ready for pipeline setup

### Phase 8: Validation ✓
- Service status check
- Resource summary
- Final validation report

---

## 🎯 Expected Output

### Success Scenario

```
=========================================
  Test Results Summary
=========================================
Completed at: Fri Jan 17 14:30:00 PST 2026

Tests Passed:   25
Tests Failed:   0
Warnings:       2

╔═══════════════════════════════════════════╗
║  ✓ DEPLOYMENT CYCLE COMPLETE!            ║
╚═══════════════════════════════════════════╝

All systems operational!

Next Steps:
  1. Access MLflow UI:     http://localhost:5000
  2. Access API Docs:      http://localhost:8000/docs
  3. Access Jenkins:       http://localhost:8080
  4. Test predictions:     python test_api.py
```

### Services Running

| Service | URL | Status |
|---------|-----|--------|
| MLflow UI | http://localhost:5000 | ✓ Running |
| API (Host) | http://localhost:8000 | ✓ Running |
| API (Docker) | http://localhost:8001 | ✓ Running |
| Jenkins | http://localhost:8080 | ✓ Running |

---

## 🔧 Manual Testing (Step by Step)

If you prefer to test each component separately:

### 1. Test Data Pipeline (2 min)

```bash
# Download and preprocess
python scripts/download_data.py
python scripts/preprocess_data.py

# Verify
ls -lh data/raw/diabetic_data.csv
ls -lh data/processed/train.csv
```

### 2. Test MLflow (1 min)

```bash
# Start MLflow
python scripts/setup_mlflow.py --action start

# Check health
curl http://localhost:5000/health

# Open UI
open http://localhost:5000
```

### 3. Test Model Training (15 min)

```bash
# Train all models
python scripts/train_models.py

# Check results in MLflow UI
open http://localhost:5000
```

### 4. Test API (3 min)

```bash
# Set environment
export MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
export MODEL_NAME="mediwatch_readmission_classifier"
export MODEL_STAGE="Production"

# Start API
cd api
uvicorn main:app --reload --port 8000

# In another terminal, test
curl http://localhost:8000/health
curl http://localhost:8000/model/info
python test_api.py

# Open docs
open http://localhost:8000/docs
```

### 5. Test Docker Build (5 min)

```bash
# Build image
docker build -t mediwatch-api:test -f api/Dockerfile .

# Run container
docker run -d --name mediwatch-test \
  -p 8001:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=mediwatch_readmission_classifier \
  -e MODEL_STAGE=Production \
  mediwatch-api:test

# Test
curl http://localhost:8001/health

# Check logs
docker logs mediwatch-test

# Cleanup
docker stop mediwatch-test
docker rm mediwatch-test
```

### 6. Test Jenkins (5 min)

```bash
# Start Jenkins
cd ci-cd
./scripts/start_jenkins.sh

# Get password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Open Jenkins
open http://localhost:8080
```

---

## 🐛 Troubleshooting

### Docker Not Running

```bash
# Start Docker Desktop
open -a Docker

# Wait and verify
sleep 30
docker info
```

### Port Already in Use

```bash
# Find and kill process
lsof -i :8000  # or :5000, :8080
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8002
```

### MLflow Not Starting

```bash
# Kill existing process
pkill -f mlflow

# Start fresh
python scripts/setup_mlflow.py --action start

# Check logs
tail -f mlflow.log
```

### API Errors

```bash
# Check logs
tail -f api.log

# Verify model exists
python << EOF
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
from mlflow.tracking import MlflowClient
client = MlflowClient()
models = client.search_registered_models()
for m in models:
    print(m.name)
EOF
```

### Container Issues

```bash
# View logs
docker logs mediwatch-api-test

# Inspect container
docker inspect mediwatch-api-test

# Restart container
docker restart mediwatch-api-test
```

---

## 📊 Success Criteria

Your deployment is successful when:

- [ ] All 8 test phases pass
- [ ] MLflow UI accessible at http://localhost:5000
- [ ] At least 1 model registered as "Production"
- [ ] API returns 200 on health check
- [ ] API serves predictions successfully
- [ ] Docker image builds without errors
- [ ] Container runs and serves API
- [ ] Jenkins container is running
- [ ] No failed tests in summary

---

## 🔄 Cleanup

To stop all services:

```bash
# Stop API
pkill -f "uvicorn api.main:app"

# Stop MLflow
pkill -f "mlflow server"

# Stop Docker containers
docker stop mediwatch-api-test jenkins mlflow
docker rm mediwatch-api-test

# Or stop Jenkins completely
cd ci-cd
docker-compose -f docker-compose.jenkins.yml down
```

To start fresh:

```bash
# Remove everything
docker-compose -f ci-cd/docker-compose.jenkins.yml down -v
rm -f mlflow.log api.log
pkill -f mlflow
pkill -f uvicorn

# Run setup again
./scripts/local_setup.sh
```

---

## 📈 Performance Benchmarks

Typical execution times on Mac (M1/M2):

| Phase | First Run | Subsequent Runs |
|-------|-----------|----------------|
| Prerequisites | 10 sec | 5 sec |
| Data Pipeline | 2 min | 10 sec |
| MLflow Setup | 10 sec | 5 sec |
| Model Training | 15 min | Skipped |
| API Testing | 30 sec | 20 sec |
| Docker Build | 5 min | 2 min (cached) |
| Jenkins Setup | 60 sec | 10 sec |
| **Total** | **25-30 min** | **5-8 min** |

---

## 🎓 Understanding the Output

### Test Status Indicators

- `✓ PASSED` (green) - Test succeeded
- `✗ FAILED` (red) - Test failed, deployment may be broken
- `⚠ WARNING` (yellow) - Minor issue, deployment may still work

### Key Metrics

- **Tests Passed**: Number of successful validation checks
- **Tests Failed**: Critical failures requiring attention
- **Warnings**: Non-critical issues to be aware of

### Service Health

Each service shows:
- **Status**: Running or Down
- **URL**: Access point
- **Logs**: Location of log files

---

## 🚀 Next Steps After Testing

1. **Configure Jenkins Pipeline**:
   ```bash
   # Get Jenkins password
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   
   # Login and create pipeline
   open http://localhost:8080
   ```

2. **Test Remote Triggering**:
   ```bash
   python ci-cd/scripts/trigger_jenkins.py \
     --job mediwatch-ci-cd \
     --deploy-mode docker \
     --wait
   ```

3. **Test Airflow Integration**:
   ```bash
   # Install Airflow
   pip install apache-airflow==2.8.0
   
   # Setup DAGs
   cp orchestration/airflow/dags/*.py ~/airflow/dags/
   
   # Start Airflow
   airflow webserver --port 8081
   airflow scheduler
   ```

4. **Test Kubernetes** (Optional):
   ```bash
   # Start minikube
   minikube start
   
   # Apply manifests
   kubectl apply -f <(cat <<EOF
   # Use manifests from docs/deployment.md
   EOF
   )
   ```

5. **Setup Monitoring**:
   ```bash
   cd monitoring/evidently
   python generate_report.py
   ```

---

## 📚 Related Documentation

- [LOCAL_BUILD_GUIDE.md](LOCAL_BUILD_GUIDE.md) - Complete build guide
- [docs/JENKINS_SETUP.md](docs/JENKINS_SETUP.md) - Jenkins configuration
- [docs/deployment.md](docs/deployment.md) - Deployment options
- [ci-cd/TESTING_GUIDE.md](ci-cd/TESTING_GUIDE.md) - Detailed testing

---

**Last Updated:** January 17, 2026  
**Test Script:** scripts/test_full_deployment.sh  
**Estimated Time:** 15-30 minutes (first run)
