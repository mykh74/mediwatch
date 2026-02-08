# MediWatch Airflow ML Pipeline Enhancement - Summary

## ✅ Completed Tasks

### 1. Enhanced Airflow DAG with KubernetesPodOperator
**File**: `orchestration/airflow/dags/mediwatch_pipeline_enhanced.py`

Created a production-ready ML pipeline that:
- Validates data availability before training
- Checks MLflow connectivity
- Executes model training in isolated Kubernetes pods
- Evaluates model performance (F1 score threshold: 0.80)
- Determines deployment eligibility
- Generates comprehensive execution reports

**Key Features**:
- ✅ Resource management (1-2GB RAM, 1-2 CPU cores)
- ✅ Automatic pod cleanup after training
- ✅ Volume mounts for data (read-only) and models (read-write)
- ✅ Service account integration for proper RBAC
- ✅ Weekly scheduling (Sunday 2 AM UTC)
- ✅ 7 orchestrated tasks with proper dependencies

### 2. RBAC Configuration
**File**: `ci-cd/kubernetes/airflow/rbac.yaml`

Configured Kubernetes RBAC to allow Airflow to:
- Create and manage training pods
- Access pod logs
- Execute commands in pods
- List persistent volume claims

**Resources Created**:
- ServiceAccount: `airflow`
- Role: `airflow-role` (pod management permissions)
- RoleBinding: `airflow-rolebinding`

**Applied to Deployments**:
- ✅ airflow-webserver
- ✅ airflow-scheduler

### 3. Trigger Script
**File**: `scripts/trigger_ml_pipeline.sh`

Created automation script that:
- Locates Airflow webserver pod
- Loads DAG from filesystem
- Unpauses DAG if needed
- Triggers manual execution
- Provides monitoring URLs

### 4. Comprehensive Documentation
**File**: `docs/ML_PIPELINE_GUIDE.md` (364 lines)

Complete implementation guide including:
- Architecture diagrams
- Task-by-task breakdown
- Usage instructions (3 triggering methods)
- Monitoring commands
- Schedule configuration
- Troubleshooting guide (6 common issues)
- Performance tuning guidance
- CI/CD integration examples
- Next steps for enhancements

## Architecture Overview

```
Airflow DAG (Weekly Schedule)
    ↓
1. Validate Data → 2. Check MLflow → 3. Notify Start
    ↓
4. KubernetesPodOperator → Training Pod Created
    ├─ Mount: mediwatch-data-pvc (50GB, read-only)
    ├─ Mount: mediwatch-models-pvc (20GB, read-write)
    ├─ Resources: 1-2GB RAM, 1-2 CPU
    └─ Auto-cleanup: Pod deleted after completion
    ↓
5. Evaluate Model (F1 ≥ 0.80?) → 6. Update API → 7. Report
```

## DAG Tasks

| Task | Type | Purpose | Key Action |
|------|------|---------|------------|
| validate_data | PythonOperator | Data validation | Check train.csv, test.csv exist |
| check_mlflow | PythonOperator | Service check | Verify MLflow /health endpoint |
| notify_training_start | PythonOperator | Logging | Record execution metadata |
| **train_model** | **KubernetesPodOperator** | **Model training** | **Run training in dedicated pod** |
| evaluate_model | PythonOperator | Quality gate | Compare metrics vs threshold |
| update_api | PythonOperator | Deployment | Trigger model reload (optional) |
| generate_report | PythonOperator | Reporting | Execution summary |

## How to Use

### Trigger the Pipeline

**Method 1 - Script** (Recommended):
```bash
./scripts/trigger_ml_pipeline.sh
```

**Method 2 - Airflow UI**:
1. Navigate to http://localhost:8080
2. Find `mediwatch_ml_pipeline_enhanced`
3. Click play button (▶️) → Trigger DAG

**Method 3 - CLI**:
```bash
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow dags trigger mediwatch_ml_pipeline_enhanced
```

### Monitor Execution

**Watch training pods**:
```bash
watch kubectl get pods -n mediwatch
# Look for: mediwatch-training-* pods
```

**View training logs**:
```bash
kubectl logs -n mediwatch -l airflow-pod-operator=mediwatch-training -f
```

**Check DAG status**:
- Airflow UI: http://localhost:8080/dags/mediwatch_ml_pipeline_enhanced/grid
- CLI: `kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- airflow dags list-runs -d mediwatch_ml_pipeline_enhanced`

## Current Status

### ✅ Successfully Deployed
- Enhanced DAG loaded in Airflow
- DAG visible in `airflow dags list` as `mediwatch_ml_pipeline_enhanced`
- RBAC configured and applied
- Service account attached to Airflow pods
- PVCs ready (mediwatch-data-pvc: 50GB, mediwatch-models-pvc: 20GB)
- Trigger script created and tested

### 📅 Scheduled Execution
- **Schedule**: Every Sunday at 2:00 AM UTC (`0 2 * * 0`)
- **Catchup**: Disabled (won't backfill past runs)
- **State**: Ready to trigger manually or run on schedule

### 🎯 Next Manual Trigger Options
1. Run trigger script: `./scripts/trigger_ml_pipeline.sh`
2. Use Airflow UI at http://localhost:8080
3. Wait for scheduled run (next Sunday 2 AM UTC)

## Training Pod Specifications

**Image**: `mediwatch-api:latest`

**Resources**:
- Memory: 1GB request, 2GB limit
- CPU: 1 core request, 2 cores limit

**Volumes**:
- `/data` → mediwatch-data-pvc (read-only)
- `/models` → mediwatch-models-pvc (read-write)

**Training Process**:
1. Load train.csv and test.csv from `/data/processed/`
2. Train GradientBoostingClassifier (100 estimators, depth=5)
3. Evaluate on test set
4. Calculate metrics: accuracy, precision, recall, F1 score
5. Save model to `/models/Gradient_Boosting.pkl`
6. Save metrics to `/models/metrics.json`
7. Pod auto-deleted upon completion

**Expected Duration**: 2-5 minutes (depends on data size)

## Model Deployment Workflow

```
Training Complete
    ↓
Metrics Saved → /models/metrics.json
    ↓
Evaluate Task Reads Metrics
    ↓
F1 Score ≥ 0.80?
    ├─ YES → deploy_model = True → Update API task runs
    └─ NO  → deploy_model = False → Skip API update
    ↓
Report Generated with Decision
```

## Files Created/Modified

| File | Lines | Purpose |
|------|-------|---------|
| `orchestration/airflow/dags/mediwatch_pipeline_enhanced.py` | 304 | Enhanced DAG with KubernetesPodOperator |
| `ci-cd/kubernetes/airflow/rbac.yaml` | 37 | RBAC for Airflow pod management |
| `scripts/trigger_ml_pipeline.sh` | 54 | Pipeline trigger automation |
| `docs/ML_PIPELINE_GUIDE.md` | 364 | Complete implementation guide |

**Total**: 759 lines of new code and documentation

## Integration Points

### With Existing Components

1. **MLflow**: Training can log experiments to MLflow (ready to implement)
2. **Evidently**: Can generate drift reports post-training (ready to implement)
3. **MediWatch API**: Model artifacts shared via PVC, API reloads on request
4. **Jenkins CI/CD**: Can trigger retraining as part of deployment pipeline

### Storage Integration

```
mediwatch-data-pvc (50GB)
├─ processed/
│  ├─ train.csv ← Training task reads
│  └─ test.csv  ← Training task reads

mediwatch-models-pvc (20GB)
├─ Gradient_Boosting.pkl ← Training task writes
├─ preprocessing_artifacts.pkl (existing)
└─ metrics.json ← Training task writes
```

## Advantages of KubernetesPodOperator Approach

✅ **Resource Isolation**: Training runs in dedicated pod with controlled resources
✅ **Scalability**: Can request more CPU/memory for training without affecting Airflow
✅ **Clean Separation**: Airflow image stays lightweight; training uses specialized image
✅ **Auto-cleanup**: Training pods deleted automatically, no resource leak
✅ **Flexibility**: Easy to switch training images or add GPU support
✅ **Debugging**: Training logs accessible independently via kubectl
✅ **Kubernetes-native**: Leverages native K8s features (PVCs, resource limits, RBAC)

## Troubleshooting Quick Reference

**DAG not visible**:
```bash
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow dags list-import-errors
```

**Training pod fails**:
```bash
kubectl describe pod -n mediwatch -l airflow-pod-operator=mediwatch-training
kubectl logs -n mediwatch -l airflow-pod-operator=mediwatch-training
```

**Permission errors**:
```bash
kubectl get sa -n mediwatch airflow
kubectl describe role -n mediwatch airflow-role
```

**Model not updating in API**:
```bash
kubectl rollout restart deployment/mediwatch-api -n mediwatch
```

## Future Enhancements

### Phase 1 - Monitoring & Tracking
- [ ] Add MLflow experiment tracking to training code
- [ ] Generate Evidently drift reports automatically
- [ ] Send Slack/email notifications on completion

### Phase 2 - Advanced Training
- [ ] Hyperparameter tuning with Optuna
- [ ] Model comparison across runs
- [ ] Automated model registry in MLflow

### Phase 3 - Production Hardening
- [ ] A/B testing support for model deployment
- [ ] Canary deployments for new models
- [ ] Automated rollback on performance degradation

### Phase 4 - Scaling
- [ ] Distributed training with Ray or Dask
- [ ] GPU support for deep learning models
- [ ] Multi-model training pipeline

## Documentation References

- **Main System Guide**: `SYSTEM_GUIDE.md` (528 lines)
- **ML Pipeline Guide**: `docs/ML_PIPELINE_GUIDE.md` (364 lines)
- **Quick Reference**: `docs/QUICK_REFERENCE.md`
- **Jenkins Integration**: `JENKINS_WORKFLOW_GUIDE.md`

## Quick Commands

```bash
# Trigger pipeline
./scripts/trigger_ml_pipeline.sh

# Monitor pods
watch kubectl get pods -n mediwatch

# View logs
kubectl logs -n mediwatch -l airflow-pod-operator=mediwatch-training -f

# Check DAG status
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow dags list | grep mediwatch

# Restart API (reload models)
kubectl rollout restart deployment/mediwatch-api -n mediwatch
```

## Success Criteria ✅

- [x] DAG created with KubernetesPodOperator
- [x] RBAC configured for pod creation
- [x] Training runs in isolated pods
- [x] Automatic resource management
- [x] Automatic pod cleanup
- [x] Model evaluation and deployment decisions
- [x] Comprehensive documentation
- [x] Trigger automation script
- [x] Weekly scheduling configured

## System Status

```
All Services Running:
├─ MediWatch API: 3 pods ✅
├─ MLflow: 1 pod ✅
├─ Airflow: 3 pods (webserver, scheduler, postgres) ✅
└─ Evidently: 1 pod ✅

Enhanced ML Pipeline:
├─ DAG Status: Active ✅
├─ Schedule: Weekly (Sunday 2 AM UTC) ✅
├─ RBAC: Configured ✅
├─ PVCs: Ready (data: 50GB, models: 20GB) ✅
└─ Trigger Script: Available ✅
```

---

**Implementation Complete! 🎉**

The MediWatch ML Pipeline is now fully enhanced with Kubernetes-native training capabilities, ready for automated weekly retraining or manual triggers.
