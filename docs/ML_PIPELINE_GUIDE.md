# Enhanced Airflow ML Pipeline - Implementation Guide

## Overview

The MediWatch ML Pipeline has been enhanced with Kubernetes-native training capabilities using the `KubernetesPodOperator`. This allows model training to run in dedicated, isolated pods with proper resource allocation.

## Architecture

### Pipeline Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │    mediwatch_ml_pipeline_enhanced DAG                   │ │
│  │  1. Validate Data  →  2. Check MLflow                  │ │
│  │  3. Notify Start   →  4. Train Model (K8s Pod)         │ │
│  │  5. Evaluate       →  6. Update API                    │ │
│  │  7. Generate Report                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │   KubernetesPodOperator               │
        │  Creates Training Pod                 │
        │  - Image: mediwatch-api:latest        │
        │  - Resources: 1-2GB RAM, 1-2 CPU      │
        │  - Volumes: data (RO), models (RW)    │
        └──────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────┐
        │   Training Pod Lifecycle              │
        │  1. Load data from PVC                │
        │  2. Train Gradient Boosting model     │
        │  3. Evaluate on test set              │
        │  4. Save model to models PVC          │
        │  5. Save metrics (JSON)               │
        │  6. Pod auto-deleted                  │
        └──────────────────────────────────────┘
```

## Setup Details

### 1. RBAC Configuration

**File**: [ci-cd/kubernetes/airflow/rbac.yaml](../ci-cd/kubernetes/airflow/rbac.yaml)

Created Kubernetes RBAC resources to allow Airflow to manage pods:
- **ServiceAccount**: `airflow`
- **Role**: `airflow-role` - Permissions to create/manage pods
- **RoleBinding**: `airflow-rolebinding` - Binds role to service account

```yaml
# Key permissions granted:
- pods: get, list, watch, create, update, patch, delete
- pods/log: get, list, watch
- pods/exec: get, create
- persistentvolumeclaims: get, list
```

### 2. Enhanced DAG Features

**File**: [orchestration/airflow/dags/mediwatch_pipeline_enhanced.py](../orchestration/airflow/dags/mediwatch_pipeline_enhanced.py)

**Key Features**:
- ✅ Data validation before training
- ✅ MLflow connectivity check
- ✅ Kubernetes-native training execution
- ✅ Model evaluation and deployment decision
- ✅ Comprehensive reporting
- ✅ Resource management (memory/CPU limits)
- ✅ Automatic pod cleanup

**Training Configuration**:
```python
- Image: mediwatch-api:latest
- Memory: 1GB request, 2GB limit
- CPU: 1 core request, 2 cores limit
- Volumes:
  - mediwatch-data-pvc (read-only)
  - mediwatch-models-pvc (read-write)
- Service Account: airflow
```

### 3. Storage Resources

**Existing PVCs** (already configured):
- `mediwatch-data-pvc`: 50GB - Training/test data
- `mediwatch-models-pvc`: 20GB - Model artifacts
- Access Mode: ReadWriteOnce (sufficient for single-node clusters)

## DAG Task Breakdown

### Task 1: validate_data
- **Type**: PythonOperator
- **Purpose**: Verify presence of train.csv and test.csv
- **Failure Action**: Stops pipeline execution

### Task 2: check_mlflow
- **Type**: PythonOperator
- **Purpose**: Ensure MLflow is accessible for experiment tracking
- **Endpoint**: `http://mlflow-service.mediwatch.svc.cluster.local:5000/health`

### Task 3: notify_training_start
- **Type**: PythonOperator
- **Purpose**: Log pipeline execution metadata

### Task 4: train_model ⭐
- **Type**: KubernetesPodOperator
- **Purpose**: Execute model training in dedicated pod
- **Process**:
  1. Load training data from `/data/processed/train.csv`
  2. Load test data from `/data/processed/test.csv`
  3. Train GradientBoostingClassifier
  4. Calculate metrics (accuracy, precision, recall, F1)
  5. Save model to `/models/Gradient_Boosting.pkl`
  6. Save metrics to `/models/metrics.json`
- **Auto-cleanup**: Pod deleted after completion

### Task 5: evaluate_model
- **Type**: PythonOperator
- **Purpose**: Determine if model meets deployment criteria
- **Criteria**: F1 Score ≥ 0.80
- **Output**: XCom variable `deploy_model` (boolean)

### Task 6: update_api
- **Type**: PythonOperator
- **Purpose**: Trigger API pods to reload models (if deployment approved)
- **Note**: Currently logs intent; can be extended to trigger rolling restart

### Task 7: generate_report
- **Type**: PythonOperator
- **Purpose**: Generate execution summary with metrics and decisions

## Usage

### Triggering the Pipeline

#### Option 1: Using the Trigger Script (Recommended)
```bash
./scripts/trigger_ml_pipeline.sh
```

This script:
1. Finds the Airflow webserver pod
2. Loads the DAG from the filesystem
3. Unpauses the DAG if needed
4. Creates a manual DAG run
5. Provides monitoring URLs

#### Option 2: Via Airflow UI
1. Navigate to http://localhost:8080
2. Find `mediwatch_ml_pipeline_enhanced`
3. Click the play button (▶️) to trigger
4. Select "Trigger DAG" from the dropdown

#### Option 3: Via Airflow CLI
```bash
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow dags trigger mediwatch_ml_pipeline_enhanced
```

### Monitoring Execution

#### Watch Pod Creation
```bash
watch kubectl get pods -n mediwatch
```

Look for: `mediwatch-training-*` pods

#### View Training Logs
```bash
# Get the training pod name
POD=$(kubectl get pods -n mediwatch -l airflow-pod-operator=mediwatch-training -o jsonpath='{.items[0].metadata.name}')

# Stream logs
kubectl logs -n mediwatch $POD -f
```

#### Check DAG Run Status
```bash
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow dags list-runs -d mediwatch_ml_pipeline_enhanced
```

#### View Task Instance Details
```bash
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow tasks list mediwatch_ml_pipeline_enhanced
```

## Schedule Configuration

**Current Schedule**: `0 2 * * 0` (Weekly on Sunday at 2 AM UTC)

### Changing the Schedule

Edit [orchestration/airflow/dags/mediwatch_pipeline_enhanced.py](../orchestration/airflow/dags/mediwatch_pipeline_enhanced.py):

```python
dag = DAG(
    'mediwatch_ml_pipeline_enhanced',
    schedule_interval='0 2 * * 0',  # <-- Modify this line
    ...
)
```

**Common Schedules**:
- Daily: `'0 2 * * *'`
- Twice daily: `'0 2,14 * * *'`
- Every 6 hours: `'0 */6 * * *'`
- Monthly: `'0 2 1 * *'`
- Disable: `None`

After changing, copy the file to Airflow:
```bash
POD=$(kubectl get pod -n mediwatch -l app=airflow-webserver -o jsonpath='{.items[0].metadata.name}')
kubectl cp orchestration/airflow/dags/mediwatch_pipeline_enhanced.py \
  mediwatch/$POD:/opt/airflow/dags/ -c webserver
```

## Troubleshooting

### Issue: DAG not appearing in UI

**Solution**:
```bash
# 1. Check if file exists
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  ls -la /opt/airflow/dags/ | grep enhanced

# 2. Check for import errors
kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
  airflow dags list-import-errors

# 3. Force DAG refresh (wait 30 seconds)
kubectl exec -n mediwatch deployment/airflow-scheduler -c scheduler -- \
  ls -la /opt/airflow/dags/
```

### Issue: Training pod fails to start

**Symptom**: Pod stuck in `Pending` or `ImagePullBackOff`

**Diagnosis**:
```bash
kubectl describe pod -n mediwatch -l airflow-pod-operator=mediwatch-training
```

**Common Causes**:
1. **Image not found**: Ensure `mediwatch-api:latest` is built and available
2. **Insufficient resources**: Check node capacity
3. **PVC not mounted**: Verify PVCs exist and are bound

**Solution**:
```bash
# Check PVCs
kubectl get pvc -n mediwatch

# Check node resources
kubectl top nodes

# Rebuild image if needed
docker build -t mediwatch-api:latest api/
```

### Issue: Permission denied errors in training pod

**Symptom**: `PermissionError` when saving model

**Solution**: Check RBAC configuration
```bash
# Verify service account
kubectl get sa -n mediwatch airflow

# Verify role binding
kubectl get rolebinding -n mediwatch airflow-rolebinding -o yaml

# Update deployments to use service account
kubectl patch deployment airflow-webserver -n mediwatch \
  -p '{"spec":{"template":{"spec":{"serviceAccountName":"airflow"}}}}'
kubectl patch deployment airflow-scheduler -n mediwatch \
  -p '{"spec":{"template":{"spec":{"serviceAccountName":"airflow"}}}}'
```

### Issue: Model not found in API after training

**Symptom**: API still uses old model

**Solution**: The models PVC is shared, but API pods cache models. Options:
1. **Rolling restart** (recommended):
   ```bash
   kubectl rollout restart deployment/mediwatch-api -n mediwatch
   ```
2. **Wait for next request**: API reloads models periodically
3. **Force reload via API** (if implemented):
   ```bash
   curl -X POST http://localhost/reload-model
   ```

## Integration with CI/CD

The enhanced pipeline can be integrated with Jenkins for automated retraining:

### Jenkins Pipeline Stage (Example)
```groovy
stage('Trigger ML Retraining') {
    steps {
        script {
            sh '''
                kubectl exec -n mediwatch deployment/airflow-webserver -c webserver -- \
                  airflow dags trigger mediwatch_ml_pipeline_enhanced
            '''
        }
    }
}
```

## Performance Considerations

### Resource Tuning

Edit the DAG to adjust resources based on data size:

```python
container_resources=k8s.V1ResourceRequirements(
    requests={'memory': '2Gi', 'cpu': '2000m'},  # Increase for large datasets
    limits={'memory': '4Gi', 'cpu': '4000m'}
),
```

### Data Volume Optimization

For large datasets:
1. Use data preprocessing to reduce size
2. Consider distributed training (Ray, Dask)
3. Use incremental learning for continuous updates

## Next Steps

1. **MLflow Integration**: Add experiment tracking within training code
2. **Evidently Integration**: Generate drift reports automatically
3. **Model Registry**: Register models in MLflow with versioning
4. **A/B Testing**: Deploy multiple model versions
5. **Hyperparameter Tuning**: Add Optuna/Ray Tune for optimization
6. **Distributed Training**: Scale to multiple nodes for large models

## Files Reference

- Enhanced DAG: `orchestration/airflow/dags/mediwatch_pipeline_enhanced.py`
- RBAC Configuration: `ci-cd/kubernetes/airflow/rbac.yaml`
- PVC Configuration: `ci-cd/kubernetes/airflow/pvcs.yaml`
- Trigger Script: `scripts/trigger_ml_pipeline.sh`
- System Guide: `SYSTEM_GUIDE.md`

## Support

For issues or questions:
1. Check Airflow UI: http://localhost:8080
2. View scheduler logs: `kubectl logs -n mediwatch deployment/airflow-scheduler -f`
3. Check this guide's troubleshooting section
4. Review Kubernetes events: `kubectl get events -n mediwatch --sort-by='.lastTimestamp'`
