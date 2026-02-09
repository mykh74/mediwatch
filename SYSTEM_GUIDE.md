# MediWatch MLOps System Guide

**Date:** February 3, 2026  
**Status:** Production-Ready  
**Environment:** Local Kubernetes (Docker Desktop)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Developer                         │
└────────────┬───────────────────────────────────┬────────────────┘
             │                                   │
             ▼                                   ▼
    ┌────────────────┐                 ┌──────────────────┐
    │  Jenkins CI/CD │                 │  kubectl / API   │
    │  localhost:8081│                 │                  │
    └────────┬───────┘                 └────────┬─────────┘
             │                                   │
             │ Trigger Build                     │ Direct Access
             ▼                                   ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              Kubernetes Cluster (mediwatch namespace)        │
    │                                                              │
    │  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐ │
    │  │ MediWatch API   │  │   MLflow     │  │   Evidently   │ │
    │  │ 3 pods          │  │   1 pod      │  │   1 pod       │ │
    │  │ localhost:80    │  │   port 5000  │  │   port 8800*  │ │
    │  │                 │  │              │  │               │ │
    │  │ • Preprocessing │  │ • Experiments│  │ • Drift Reports│ │
    │  │ • Predictions   │  │ • Model Reg. │  │ • Data Quality│ │
    │  │ • Model Loading │  │              │  │               │ │
    │  └─────────────────┘  └──────────────┘  └───────────────┘ │
    │                                                              │
    │  ┌──────────────────────────────────────────────────────┐  │
    │  │              Apache Airflow (3 pods)                 │  │
    │  │              localhost:8080                          │  │
    │  │                                                       │  │
    │  │  • Webserver: UI and API                            │  │
    │  │  • Scheduler: DAG execution                         │  │
    │  │  • PostgreSQL: Metadata storage                     │  │
    │  └──────────────────────────────────────────────────────┘  │
    │                                                              │
    │  * Requires port-forward for external access                │
    └─────────────────────────────────────────────────────────────┘
```

## 🎯 System Components

### 1. **MediWatch API** (FastAPI)
- **Status:** ✅ Running (3 pods)
- **Access:** http://localhost (port 80)
- **Documentation:** http://localhost/docs
- **Features:**
  - Accepts raw patient data (no preprocessing needed)
  - Automatic feature transformation using preprocessing artifacts
  - Gradient Boosting model for readmission prediction
  - Health checks and monitoring endpoints
  - Horizontal Pod Autoscaler (2-10 replicas)

**Key Endpoints:**
```bash
# Health check
GET http://localhost/health

# Prediction (raw data)
POST http://localhost/predict
POST http://localhost/api/v1/predict

# Batch prediction
POST http://localhost/api/v1/predict/batch

# Model info
GET http://localhost/model/info
```

### 2. **MLflow** (Experiment Tracking)
- **Status:** ✅ Running (1 pod)
- **Access:** Internal only (port 5000)
- **Storage:** SQLite backend + PVC
- **Features:**
  - Experiment tracking
  - Model registry
  - Model versioning
  - Metrics logging

**Access via Port Forward:**
```bash
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000
# Then visit: http://localhost:5000
```

### 3. **Apache Airflow** (Orchestration)
- **Status:** ✅ Running (3 pods)
- **Access:** http://localhost:8080
- **Credentials:** admin / admin
- **Features:**
  - DAG scheduling and execution
  - LocalExecutor with PostgreSQL backend
  - System validation pipeline (working)

**Available DAGs:**
- `mediwatch_ml_pipeline_simple` ✅ - System validation via API calls
- `mediwatch_ml_pipeline` ⏸️ - Full training pipeline (requires ML packages)

### 4. **Evidently** (Data Monitoring)
- **Status:** ✅ Running (1 pod)
- **Access:** http://localhost:8800 (via port-forward)
- **Features:**
  - Data drift detection
  - Data quality monitoring
  - HTML report generation
  - Report storage in PVC

**Usage:**
```bash
# List reports
curl http://localhost:8800/reports

# View report
open http://localhost:8800/reports/{report_name}

# Upload report
curl -X POST -F "file=@report.html" http://localhost:8800/upload-report
```

### 5. **Jenkins CI/CD** (Automation)
- **Status:** ✅ Running (Docker container)
- **Access:** http://localhost:8081
- **Credentials:** admin / admin
- **Features:**
  - Automated Docker image builds
  - Kubernetes deployment
  - Rolling updates
  - Smoke tests

**Pipeline Stages:**
1. Initialization
2. Checkout from GitHub
3. Environment Validation
4. Docker Image Build
5. API Tests
6. Deploy to Kubernetes
7. Smoke Test Deployment

## 📊 Resource Status

```bash
kubectl get all -n mediwatch
```

**Current Resources:**
- **Deployments:** 6 (API, MLflow, Airflow x3, Evidently)
- **Pods:** 8 running
- **Services:** 6 (3 LoadBalancer, 3 ClusterIP)
- **PVCs:** 8 (total 210GB storage)
- **HPA:** 1 (MediWatch API autoscaling)

## 🚀 Quick Start Guide

### Initial Setup
```bash
# 1. Start Docker Desktop with Kubernetes enabled
# 2. Verify cluster access
kubectl cluster-info

# 3. Check namespace
kubectl get ns mediwatch

# 4. Start port forwards (use setup script)
./scripts/setup_port_forwards.sh

# 5. Verify all services
kubectl get pods -n mediwatch
```

### Making Predictions

**Example 1: Single Prediction**
```bash
curl -X POST "http://localhost/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "race": "Caucasian",
    "gender": "Female",
    "age": "[60-70)",
    "time_in_hospital": 3,
    "num_lab_procedures": 50,
    "num_procedures": 1,
    "num_medications": 15,
    "number_outpatient": 0,
    "number_emergency": 0,
    "number_inpatient": 0,
    "diag_1": 250.83,
    "diag_2": 250.01,
    "diag_3": 255,
    "number_diagnoses": 9,
    "max_glu_serum": "None",
    "A1Cresult": "None",
    "change": "Ch",
    "diabetesMed": "Yes"
  }'
```

**Example 2: Batch Prediction**
```python
import requests

data = [
    {"race": "Caucasian", "gender": "Male", "age": "[50-60)", ...},
    {"race": "AfricanAmerican", "gender": "Female", "age": "[70-80)", ...}
]

response = requests.post(
    "http://localhost/api/v1/predict/batch",
    json={"patients": data}
)
print(response.json())
```

## 🔄 CI/CD Workflow

### Automated Deployment via Jenkins

**Trigger Build:**
1. Open http://localhost:8081
2. Select "MediWatch-Deploy"
3. Click "Build with Parameters"
4. Set DEPLOY_MODE: `kubernetes`
5. Set RUN_TESTS: `true`
6. Click "Build"

**What Happens:**
```
Code → Jenkins → Docker Build → Tests → Kubernetes Deploy → Rolling Update
```

**Manual Deployment:**
```bash
# 1. Build new image
docker build -t mediwatch-api:latest -f api/Dockerfile .

# 2. Trigger rolling update
kubectl rollout restart deployment/mediwatch-api -n mediwatch

# 3. Monitor rollout
kubectl rollout status deployment/mediwatch-api -n mediwatch

# 4. Verify new pods
kubectl get pods -n mediwatch -l app=mediwatch-api
```

### Rollback if Needed
```bash
# View deployment history
kubectl rollout history deployment/mediwatch-api -n mediwatch

# Rollback to previous version
kubectl rollout undo deployment/mediwatch-api -n mediwatch

# Rollback to specific revision
kubectl rollout undo deployment/mediwatch-api -n mediwatch --to-revision=5
```

## 📈 Monitoring & Operations

### Check Service Health
```bash
# API health
curl http://localhost/health

# MLflow (requires port-forward)
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000 &
curl http://localhost:5000/health

# Evidently (requires port-forward)
kubectl port-forward -n mediwatch svc/evidently-service 8800:8000 &
curl http://localhost:8800/health

# Airflow
curl http://localhost:8080/health
```

### View Logs
```bash
# API logs (all pods)
kubectl logs -n mediwatch -l app=mediwatch-api --tail=50

# Specific pod
kubectl logs -n mediwatch mediwatch-api-ff6d74c68-6r24f

# Follow logs in real-time
kubectl logs -n mediwatch -l app=mediwatch-api -f

# Airflow scheduler
kubectl logs -n mediwatch -l component=scheduler
```

### Scale Services
```bash
# Scale API manually
kubectl scale deployment mediwatch-api -n mediwatch --replicas=5

# Check HPA status
kubectl get hpa -n mediwatch

# View HPA events
kubectl describe hpa mediwatch-api-hpa -n mediwatch
```

### Resource Usage
```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods -n mediwatch

# Specific deployment
kubectl top pods -n mediwatch -l app=mediwatch-api
```

## 🔍 Troubleshooting

### Pod Issues
```bash
# Check pod status
kubectl get pods -n mediwatch

# Describe pod for events
kubectl describe pod <pod-name> -n mediwatch

# Check pod events
kubectl get events -n mediwatch --sort-by='.lastTimestamp'

# Shell into pod
kubectl exec -it <pod-name> -n mediwatch -- /bin/bash
```

### Service Issues
```bash
# Check service endpoints
kubectl get endpoints -n mediwatch

# Test service from inside cluster
kubectl run test-pod --rm -it --image=curlimages/curl -n mediwatch -- \
  curl http://mediwatch-api-service/health

# Describe service
kubectl describe svc mediwatch-api-service -n mediwatch
```

### Common Issues

**Issue: API pods not ready**
```bash
# Check if models are loaded
kubectl logs -n mediwatch -l app=mediwatch-api --tail=20 | grep -i "model"

# Copy models if missing
kubectl cp models/ mediwatch/<pod-name>:/app/models/
```

**Issue: Evidently CrashLoopBackOff**
```bash
# Already fixed - python-multipart added to deployment
kubectl logs -n mediwatch -l app=evidently
```

**Issue: Port forward connection refused**
```bash
# Kill existing port-forwards
pkill -f "port-forward"

# Restart with correct service
kubectl port-forward -n mediwatch svc/<service-name> <local>:<remote>
```

## 🗂️ File Structure

```
MediWatch/
├── api/                          # FastAPI application
│   ├── main.py                   # API with preprocessing
│   └── Dockerfile                # Container definition
├── ci-cd/
│   ├── kubernetes/               # K8s manifests
│   │   ├── api/
│   │   ├── mlflow/
│   │   ├── evidently/
│   │   └── airflow/
│   └── jenkins/                  # Jenkins setup
├── data/
│   ├── raw/                      # Original data
│   └── processed/                # Train/test splits
├── models/                       # Trained models
│   ├── Gradient_Boosting.pkl     # Best model
│   └── preprocessing_artifacts.pkl
├── monitoring/
│   └── evidently/
│       ├── generate_report.py    # Report generation
│       └── test_evidently_upload.py
├── orchestration/
│   └── airflow/
│       └── dags/
│           ├── mediwatch_pipeline_simple.py  ✅
│           └── mediwatch_ml_pipeline.py      ⏸️
├── scripts/
│   ├── setup_port_forwards.sh    # Port forward automation
│   └── test_full_deployment.sh
├── Jenkinsfile                   # CI/CD pipeline
└── SYSTEM_GUIDE.md              # This file
```

## 🔐 Credentials & Access

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Jenkins | http://localhost:8081 | admin | admin |
| Airflow | http://localhost:8080 | admin | admin |
| API | http://localhost | - | - |
| MLflow | http://localhost:5000* | - | - |
| Evidently | http://localhost:8800* | - | - |

*Requires port-forward

## 📝 Common Tasks

### Task 1: Deploy Code Changes
```bash
# 1. Make changes to api/main.py
# 2. Commit changes
git add api/main.py
git commit -m "Updated API logic"
git push

# 3. Trigger Jenkins build (UI or API)
# 4. Watch deployment
kubectl get pods -n mediwatch -l app=mediwatch-api -w
```

### Task 2: Update Model
```bash
# 1. Train new model (save to models/)
# 2. Copy to all API pods
for pod in $(kubectl get pods -n mediwatch -l app=mediwatch-api -o name); do
  kubectl cp models/Gradient_Boosting.pkl mediwatch/$pod:/app/models/
done

# 3. Restart pods to reload
kubectl rollout restart deployment/mediwatch-api -n mediwatch
```

### Task 3: Generate Drift Report
```bash
# Using the test script
python monitoring/evidently/test_evidently_upload.py

# View report
open http://localhost:8800/reports/data_drift_report.html
```

### Task 4: Debug API Issue
```bash
# 1. Check pod status
kubectl get pods -n mediwatch -l app=mediwatch-api

# 2. View recent logs
kubectl logs -n mediwatch -l app=mediwatch-api --tail=100

# 3. Check health endpoint
curl http://localhost/health

# 4. Shell into pod
kubectl exec -it <pod-name> -n mediwatch -- /bin/bash
ls -la /app/models/
python -c "import joblib; m = joblib.load('/app/models/Gradient_Boosting.pkl'); print(m)"
```

## 🎓 Best Practices

1. **Always use Jenkins for deployments** - Ensures consistent, tested builds
2. **Monitor logs after deployments** - Catch issues early
3. **Use rolling updates** - Zero-downtime deployments
4. **Test locally before pushing** - Run API tests with `pytest`
5. **Keep models versioned in MLflow** - Track model performance
6. **Generate drift reports regularly** - Detect data quality issues
7. **Scale conservatively** - HPA handles most traffic patterns
8. **Backup data regularly** - PVCs contain important data

## 🚨 Emergency Procedures

### Complete System Restart
```bash
# 1. Stop all services
kubectl delete namespace mediwatch

# 2. Recreate namespace
kubectl create namespace mediwatch

# 3. Redeploy
kubectl apply -f ci-cd/kubernetes/
```

### API Emergency Rollback
```bash
# Immediate rollback to previous version
kubectl rollout undo deployment/mediwatch-api -n mediwatch
```

### Clear All Port Forwards
```bash
pkill -f "port-forward"
```

## 📚 Additional Resources

- **Kubernetes Docs:** https://kubernetes.io/docs/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **MLflow Docs:** https://mlflow.org/docs/latest/
- **Airflow Docs:** https://airflow.apache.org/docs/
- **Evidently Docs:** https://docs.evidentlyai.com/

---

**Last Updated:** February 3, 2026  
**Maintained By:** Michael Kuzmyn  
**System Version:** v1.0
