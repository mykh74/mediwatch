# MediWatch Complete MLOps Workflow

## 🎯 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KUBERNETES CLUSTER                                  │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        NAMESPACE: mediwatch                         │    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐│    │
│  │  │ MediWatch API│  │    MLflow    │  │  Evidently   │  │Airflow ││    │
│  │  │  (3 pods)    │  │  (tracking)  │  │ (monitoring) │  │Orchest.││    │
│  │  │              │  │              │  │              │  │        ││    │
│  │  │ Port: 30080  │  │ Port: 30500  │  │ Port: 30800  │  │30411   ││    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┬───┘│    │
│  │         │                 │                 │                │     │    │
│  │         └─────────────────┴─────────────────┴────────────────┘     │    │
│  │                                  │                                  │    │
│  │         ┌────────────────────────┴───────────────────────┐        │    │
│  │         │      Persistent Volume Claims (210GB)          │        │    │
│  │         │  Models │ Data │ Experiments │ Reports         │        │    │
│  │         └─────────────────────────────────────────────────┘        │    │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         JENKINS CI/CD SERVER                                 │
│                         (Port 8080)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow: Development to Production

### **Phase 1: Initial Development (Local)**

```
Developer's Machine
└─→ 1. Write/modify ML code
    └─→ 2. Test in Jupyter notebooks
        └─→ 3. Commit to Git
            └─→ 4. Trigger Jenkins
```

---

### **Phase 2: CI/CD Pipeline (Jenkins)**

```
┌─────────────────────────────────────────────────────────────────┐
│                     JENKINS PIPELINE                            │
│                                                                 │
│  Stage 1: Checkout Code                                        │
│  ↓                                                              │
│  Stage 2: Build Docker Image                                   │
│  │   - Build mediwatch-api:${BUILD_NUMBER}                     │
│  │   - Include trained models & preprocessing artifacts        │
│  ↓                                                              │
│  Stage 3: Validate Model                                       │
│  │   - Check MLflow for production model                       │
│  │   - Verify model metrics meet thresholds                    │
│  ↓                                                              │
│  Stage 4: Run Tests                                            │
│  │   - Unit tests                                              │
│  │   - API endpoint tests                                      │
│  │   - Integration tests                                       │
│  ↓                                                              │
│  Stage 5: Deploy (docker OR kubernetes)                        │
│  │                                                              │
│  │   OPTION A: Docker Mode                                     │
│  │   └─→ docker-compose up -d                                  │
│  │                                                              │
│  │   OPTION B: Kubernetes Mode                                 │
│  │   └─→ kubectl apply -f k8s/                                 │
│  │   └─→ Deploy API, MLflow, Evidently, Airflow               │
│  ↓                                                              │
│  Stage 6: Health Check                                         │
│  │   - Test all deployed services                              │
│  │   - Verify API responds correctly                           │
│  ↓                                                              │
│  Stage 7: Notify                                               │
│  └─→ Send deployment status                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Jenkins Triggers:**
- Manual: Click "Build with Parameters" in UI
- Git webhook: On push to main branch
- API call: `curl http://jenkins:8080/job/mediwatch-ci-cd/build`
- Airflow: Triggered by deployment DAG task

---

### **Phase 3: ML Pipeline Orchestration (Airflow)**

```
┌───────────────────────────────────────────────────────────────────┐
│              AIRFLOW DAG: mediwatch_ml_pipeline                   │
│                  Schedule: @weekly (or manual)                    │
│                                                                   │
│  Task 1: Download Data                                           │
│  │   - Get latest dataset from Kaggle                            │
│  │   - Save to /data/raw/                                        │
│  ↓                                                                │
│  Task 2: Preprocess Data                                         │
│  │   - Clean & transform features                                │
│  │   - Save preprocessing artifacts (*.pkl)                      │
│  │   - Create train/test splits                                  │
│  │   - Save to /data/processed/                                  │
│  ↓                                                                │
│  Task 3: Train Baseline Models                                   │
│  │   - Train 6 models:                                           │
│  │     • Logistic Regression                                     │
│  │     • Random Forest                                           │
│  │     • Gradient Boosting                                       │
│  │     • XGBoost                                                 │
│  │     • LightGBM                                                │
│  │     • CatBoost                                                │
│  │   - Log experiments to MLflow →───────────┐                  │
│  ↓                                            │                  │
│  Task 4: Hyperparameter Optimization         │                  │
│  │   - Use Ray Tune for HPO                  │                  │
│  │   - Search best hyperparameters           │                  │
│  │   - Log to MLflow →───────────────────────┼──→ MLflow        │
│  ↓                                            │                  │
│  Task 5: Evaluate Models                     │                  │
│  │   - Compare all models                    │                  │
│  │   - Calculate metrics →───────────────────┘                  │
│  ↓                                                                │
│  Task 6: Register Best Model                                     │
│  │   - Select best performing model                             │
│  │   - Register to MLflow Model Registry                        │
│  │   - Tag as "Staging"                                          │
│  ↓                                                                │
│  Task 7: Validate Model                                          │
│  │   - Run validation checks                                     │
│  │   - If passed: promote to "Production"                       │
│  ↓                                                                │
│  Task 8: Monitor for Drift                                       │
│  │   - Run Evidently checks →────────────────→ Evidently        │
│  │   - Detect data/target drift                                 │
│  │   - Generate reports                                          │
│  ↓                                                                │
│  Task 9: Trigger Deployment (Optional)                           │
│  └─→ Call Jenkins API to redeploy with new model                │
└───────────────────────────────────────────────────────────────────┘
```

**Airflow Features:**
- **Web UI**: http://localhost:30411 (Kubernetes) or http://localhost:8080 (local)
- **Scheduling**: Run pipeline weekly or on-demand
- **Monitoring**: Track task success/failure, execution time
- **Retry logic**: Auto-retry failed tasks
- **Dependencies**: Ensures tasks run in correct order

---

### **Phase 4: Experiment Tracking (MLflow)**

```
┌─────────────────────────────────────────────────────────────┐
│                    MLflow Tracking Server                    │
│                   Port: 30500 (Kubernetes)                   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │            Experiment Tracking                      │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ Experiment: mediwatch-readmission            │  │    │
│  │  │                                               │  │    │
│  │  │  Run 1: Logistic Regression                  │  │    │
│  │  │  - Parameters: C=1.0, penalty='l2'           │  │    │
│  │  │  - Metrics: F1=0.45, AUC=0.62               │  │    │
│  │  │  - Artifacts: model.pkl                      │  │    │
│  │  │                                               │  │    │
│  │  │  Run 2: Random Forest                        │  │    │
│  │  │  - Parameters: n_estimators=100, depth=10    │  │    │
│  │  │  - Metrics: F1=0.48, AUC=0.65               │  │    │
│  │  │                                               │  │    │
│  │  │  Run 3: Gradient Boosting ⭐ BEST            │  │    │
│  │  │  - Parameters: n_estimators=200, lr=0.1      │  │    │
│  │  │  - Metrics: F1=0.53, AUC=0.67               │  │    │
│  │  │  - Artifacts: model.pkl, preprocessor.pkl   │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Model Registry                         │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ Model: mediwatch_readmission_classifier      │  │    │
│  │  │                                               │  │    │
│  │  │  Version 1: Staging                          │  │    │
│  │  │  - Source: Run 3 (Gradient Boosting)         │  │    │
│  │  │  - F1 Score: 0.53                            │  │    │
│  │  │                                               │  │    │
│  │  │  Version 2: Production ✅                    │  │    │
│  │  │  - Source: Run 3 (Gradient Boosting)         │  │    │
│  │  │  - F1 Score: 0.53, AUC: 0.67                │  │    │
│  │  │  - Status: Active                            │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**MLflow Capabilities:**
- Compare all experiments side-by-side
- Track hyperparameters, metrics, artifacts
- Version control for models
- API to retrieve production models
- Artifact storage (models, preprocessors)

---

### **Phase 5: Model Serving (MediWatch API)**

```
┌──────────────────────────────────────────────────────────────┐
│              MediWatch API (FastAPI)                         │
│              Port: 30080 (Kubernetes)                        │
│                                                              │
│  Startup Process:                                           │
│  1. Load production model from MLflow                       │
│  2. Load preprocessing artifacts                            │
│  3. Initialize FastAPI app                                  │
│  4. Ready to serve predictions                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Endpoints:                                         │    │
│  │                                                      │    │
│  │  GET /health                                        │    │
│  │  └─→ Status: healthy, model_loaded: true           │    │
│  │                                                      │    │
│  │  GET /model/info                                    │    │
│  │  └─→ Model name, version, metrics                  │    │
│  │                                                      │    │
│  │  POST /predict                                      │    │
│  │  └─→ Input: Patient data (JSON)                    │    │
│  │      Output: Readmission prediction + probability  │    │
│  │                                                      │    │
│  │  POST /predict/batch                                │    │
│  │  └─→ Input: Multiple patients                      │    │
│  │      Output: Array of predictions                  │    │
│  │                                                      │    │
│  │  GET /docs (Swagger UI)                             │    │
│  │  └─→ Interactive API documentation                 │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘

Request Flow:
1. Client sends POST /predict with patient data
2. API applies preprocessing (same artifacts from training)
3. Model makes prediction
4. API returns: {"prediction": 0/1, "probability": 0.75}
5. Response logged for monitoring
```

---

### **Phase 6: Monitoring & Drift Detection (Evidently)**

```
┌─────────────────────────────────────────────────────────────┐
│              Evidently Monitoring Service                    │
│              Port: 30800 (Kubernetes)                        │
│                                                              │
│  Monitoring Tasks (Triggered by Airflow):                   │
│                                                              │
│  1. Data Drift Detection                                    │
│     ┌───────────────────────────────────────┐             │
│     │ Compare: Training Data vs New Data    │             │
│     │                                        │             │
│     │ Checked Features:                      │             │
│     │ • age: No drift ✅                     │             │
│     │ • num_medications: Drift detected ⚠️   │             │
│     │ • time_in_hospital: No drift ✅        │             │
│     │ • num_procedures: Drift detected ⚠️    │             │
│     │                                        │             │
│     │ Tests: KS test, PSI, Wasserstein      │             │
│     └───────────────────────────────────────┘             │
│                                                              │
│  2. Target Drift Detection                                  │
│     ┌───────────────────────────────────────┐             │
│     │ Compare: Training vs Production        │             │
│     │                                        │             │
│     │ Readmission rate:                      │             │
│     │ • Training: 35%                        │             │
│     │ • Production: 42% ⚠️ DRIFT DETECTED    │             │
│     │                                        │             │
│     │ Action: Trigger model retraining      │             │
│     └───────────────────────────────────────┘             │
│                                                              │
│  3. Model Performance Monitoring                            │
│     ┌───────────────────────────────────────┐             │
│     │ Metrics Over Time:                     │             │
│     │ • Accuracy: Declining trend ⚠️         │             │
│     │ • F1 Score: Stable ✅                  │             │
│     │ • Prediction latency: Normal ✅        │             │
│     └───────────────────────────────────────┘             │
│                                                              │
│  Output:                                                     │
│  • HTML reports with visualizations                         │
│  • Alerts sent to Airflow/Jenkins                          │
│  • Stored in /reports/ directory                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔁 Complete End-to-End Flow

### **Weekly Automated Cycle**

```
Sunday 00:00 AM
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 1: Airflow Trigger (Scheduled)                       │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 2: Download Latest Data                              │
│ • Kaggle API downloads newest dataset                     │
│ • Saved to Kubernetes PVC: mediwatch-data-pvc             │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 3: Preprocess Data                                   │
│ • Apply transformations (encoding, scaling)               │
│ • Save preprocessing artifacts to PVC                     │
│ • Create train/test splits                                │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 4: Train Models                                      │
│ • Train 6 baseline models in parallel                     │
│ • Log all experiments to MLflow                           │
│ • MLflow stores in PVC: mlflow-data-pvc                   │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 5: Hyperparameter Optimization                       │
│ • Ray Tune runs HPO on best model                         │
│ • Tests different configurations                          │
│ • Logs results to MLflow                                  │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 6: Evaluate & Select Best Model                      │
│ • Compare all models by F1 score                          │
│ • Best model: Gradient Boosting (F1=0.53)                │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 7: Register Model                                    │
│ • Register in MLflow Model Registry                       │
│ • Initial stage: "Staging"                                │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 8: Validate Model                                    │
│ • Run validation tests                                    │
│ • Check: F1 > 0.5 ✅                                       │
│ • Promote to "Production"                                 │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 9: Drift Monitoring                                  │
│ • Evidently compares new data vs training data            │
│ • Generates drift report                                  │
│ • Saves to PVC: evidently-reports-pvc                     │
└───────────────────────────────────────────────────────────┘
    ↓
    IF new model is better OR drift detected:
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 10: Trigger Jenkins Deployment                       │
│ • Airflow calls Jenkins API                               │
│ • Jenkins builds new Docker image with new model          │
│ • Deploys to Kubernetes                                   │
│ • Updates MediWatch API pods (rolling update)             │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Step 11: Health Check                                     │
│ • Kubernetes readiness probes                             │
│ • API responds to /health                                 │
│ • All 3 API pods running with new model ✅                │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ Done! New model serving predictions                       │
└───────────────────────────────────────────────────────────┘
```

---

## 🎮 User Interactions

### **Data Scientist:**
```
1. Develop new features in Jupyter notebook
2. Test locally with sample data
3. Update code in src/mediwatch/
4. Commit to Git
5. Jenkins automatically builds & tests
6. Airflow retrains with new features
7. MLflow tracks all experiments
8. Review results in MLflow UI
```

### **MLOps Engineer:**
```
1. Monitor Airflow DAG execution
2. Check Jenkins pipeline status
3. Review Evidently drift reports
4. Scale Kubernetes resources if needed
5. Update deployment configurations
6. Manage MLflow model registry
```

### **Application User/Client:**
```
1. Send POST request to MediWatch API
   curl -X POST http://localhost:30080/predict \
     -H "Content-Type: application/json" \
     -d '{"age": 65, "num_medications": 15, ...}'

2. Receive prediction response
   {"prediction": 1, "probability": 0.78}

3. Application uses prediction for decision-making
```

---

## 📊 Component Communication

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│          │      │          │      │          │      │          │
│ Airflow  │─────→│  MLflow  │←─────│ Jenkins  │─────→│   API    │
│          │ logs │          │reads │          │deploy│          │
└─────┬────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
      │                │                 │                  │
      │ triggers       │ stores          │ builds           │ logs
      │                │                 │                  │
      ↓                ↓                 ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│              Kubernetes Persistent Storage                       │
│  • Models  • Experiments  • Logs  • Reports  • Data             │
└─────────────────────────────────────────────────────────────────┘
      ↑                                                      │
      │ monitors                                             │ reads
      │                                                      ↓
┌─────┴────┐                                          ┌──────────┐
│          │                                          │          │
│Evidently │                                          │  Users   │
│          │                                          │ (HTTP)   │
└──────────┘                                          └──────────┘
```

### **Data Flow:**
1. **Training Data**: Raw → Airflow → Processed → MLflow
2. **Models**: MLflow Registry → Jenkins → Docker Image → Kubernetes → API Pods
3. **Predictions**: User → API → Model → Response → Logs
4. **Monitoring**: API Logs → Evidently → Drift Reports → Airflow

---

## 🚀 Deployment Options

### **Option 1: Full Kubernetes (Production)**
- All services in Kubernetes cluster
- High availability (3 API replicas)
- Auto-scaling enabled
- Persistent storage
- Best for: Production environments

### **Option 2: Docker Compose (Development)**
- All services as Docker containers
- Easy local testing
- Simpler networking
- Less resource intensive
- Best for: Development/testing

### **Option 3: Hybrid**
- Jenkins on host machine
- Services in Kubernetes
- Easy CI/CD access
- Best for: Testing K8s deployments

---

## 🔐 Access URLs (Kubernetes Deployment)

| Service | Internal | External (NodePort) | Purpose |
|---------|----------|---------------------|---------|
| MediWatch API | http://mediwatch-api:8000 | http://localhost:30080 | Predictions |
| MLflow | http://mlflow:5000 | http://localhost:30500 | Experiments |
| Evidently | http://evidently:8080 | http://localhost:30800 | Monitoring |
| Airflow | http://airflow-webserver:8080 | http://localhost:30411 | Orchestration |
| Jenkins | - | http://localhost:8080 | CI/CD |

---

## 📈 Success Metrics

### **System Health:**
- ✅ All pods running (no CrashLoopBackOff)
- ✅ API response time < 200ms
- ✅ Pipeline success rate > 95%
- ✅ Zero downtime deployments

### **ML Performance:**
- ✅ Model F1 score > 0.50
- ✅ Data drift detected within 24 hours
- ✅ New models deployed within 1 hour
- ✅ All experiments tracked in MLflow

---

## 🛠️ Troubleshooting Flow

```
Issue Reported
    ↓
Check Kubernetes Pods
kubectl get pods -n mediwatch
    ↓
    ├─→ Pod CrashLoopBackOff?
    │   └─→ Check logs: kubectl logs <pod>
    │       └─→ Fix: Missing model, config error, resource limits
    │
    ├─→ API not responding?
    │   └─→ Check health: curl localhost:30080/health
    │       └─→ Fix: Model not loaded, MLflow unreachable
    │
    ├─→ Airflow DAG failing?
    │   └─→ Check Airflow UI logs
    │       └─→ Fix: Data missing, credentials, dependencies
    │
    └─→ Jenkins build failing?
        └─→ Check console output
            └─→ Fix: Docker permissions, image errors, tests failing
```

---

## 🎯 Next Steps

To get this workflow running:

1. **Start with local development**
   ```bash
   python scripts/download_data.py
   python scripts/preprocess_data.py
   python scripts/train_models.py
   ```

2. **Test API locally**
   ```bash
   uvicorn api.main:app --reload
   ```

3. **Setup Jenkins**
   ```bash
   cd ci-cd
   docker-compose -f docker-compose.jenkins.yml up -d
   ```

4. **Deploy to Kubernetes**
   ```bash
   kubectl create namespace mediwatch
   kubectl apply -f k8s/
   ```

5. **Configure Airflow**
   - Access UI at http://localhost:30411
   - Enable mediwatch_ml_pipeline DAG
   - Trigger manual run

6. **Monitor & Iterate**
   - Check MLflow experiments
   - Review Evidently reports
   - Optimize based on metrics

---

**Status**: 📋 Architecture complete, ready for implementation!
