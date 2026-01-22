# MediWatch MLOps Stack - Complete Guide

This guide covers the complete Kubernetes deployment of the MediWatch MLOps infrastructure.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     MediWatch MLOps Stack                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  API (x3)    │  │   MLflow     │  │  Evidently   │        │
│  │  Port: 80    │  │  Port: 5000  │  │  Port: 8001  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                  │                  │                 │
│         └──────────────────┴──────────────────┘                │
│                           │                                     │
│  ┌────────────────────────┴────────────────────────┐          │
│  │              Airflow Orchestration               │          │
│  │  Webserver (8080) │ Scheduler │ PostgreSQL      │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  ┌─────────────────────────────────────────────────┐          │
│  │         Persistent Storage (200GB Total)         │          │
│  │  Models │ Data │ MLflow │ Airflow │ Evidently   │          │
│  └─────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. MediWatch API (FastAPI)
- **Replicas**: 3 (auto-scales 2-10)
- **Endpoint**: http://localhost/
- **Features**: 
  - Health monitoring
  - Model inference
  - API documentation at `/docs`
- **Storage**: 70GB (models + data)

### 2. MLflow Tracking Server
- **Replicas**: 1
- **Endpoint**: Port-forward to 5000
- **Features**:
  - Experiment tracking
  - Model registry
  - Artifact storage
- **Storage**: 100GB
- **Backend**: SQLite

### 3. Apache Airflow
- **Components**:
  - Webserver (UI)
  - Scheduler (task execution)
  - PostgreSQL (metadata)
- **Endpoint**: Port-forward to 8080
- **Features**:
  - Workflow orchestration
  - DAG scheduling
  - Task monitoring
- **Storage**: 25GB (PostgreSQL 10GB, DAGs 5GB, Logs 10GB)
- **Credentials**: admin / admin

### 4. Evidently Monitoring
- **Replicas**: 1
- **Endpoint**: Port-forward to 8001
- **Features**:
  - ML model monitoring
  - Data drift detection
  - Report generation
- **Storage**: 15GB (reports 5GB, data 10GB)

## Quick Start

### Deploy Full Stack

```bash
# Via Jenkins (Recommended)
1. Go to http://localhost:8080/job/mediwatch-ci-cd/
2. Click "Build with Parameters"
3. Select DEPLOY_MODE: kubernetes
4. Click "Build"

# Manual deployment
cd /Users/michaelkuzmyn/projects/ik/MediWatch
./ci-cd/kubernetes/deploy.sh latest
```

### Access Services

```bash
# API (LoadBalancer - automatically available)
curl http://localhost/health
open http://localhost/docs

# MLflow (Port-forward required)
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000
open http://localhost:5000

# Airflow (Port-forward required)
kubectl port-forward -n mediwatch svc/airflow-webserver-service 8080:8080
open http://localhost:8080
# Login: admin / admin

# Evidently (Port-forward required)
kubectl port-forward -n mediwatch svc/evidently-service 8001:8000
open http://localhost:8001
```

## Storage Configuration

| Component | PVC Name | Size | Purpose |
|-----------|----------|------|---------|
| API Models | mediwatch-models-pvc | 20GB | ML model artifacts |
| API Data | mediwatch-data-pvc | 50GB | Training/inference data |
| MLflow | mlflow-data-pvc | 100GB | Experiments & artifacts |
| Airflow DB | airflow-postgres-pvc | 10GB | Metadata database |
| Airflow DAGs | airflow-dags-pvc | 5GB | Workflow definitions |
| Airflow Logs | airflow-logs-pvc | 10GB | Execution logs |
| Evidently Reports | evidently-reports-pvc | 5GB | Monitoring reports |
| Evidently Data | evidently-data-pvc | 10GB | Reference datasets |

**Total Storage**: 210GB

## Monitoring

### Check All Resources

```bash
# Overview
kubectl get all -n mediwatch

# Pods status
kubectl get pods -n mediwatch -w

# Services and endpoints
kubectl get svc -n mediwatch

# Storage usage
kubectl get pvc -n mediwatch

# Auto-scaling status
kubectl get hpa -n mediwatch
```

### Check Logs

```bash
# API logs
kubectl logs -n mediwatch -l app=mediwatch-api --tail=100

# MLflow logs
kubectl logs -n mediwatch -l app=mlflow --tail=100

# Airflow webserver logs
kubectl logs -n mediwatch -l app=airflow-webserver --tail=100

# Airflow scheduler logs
kubectl logs -n mediwatch -l app=airflow-scheduler --tail=100

# Evidently logs
kubectl logs -n mediwatch -l app=evidently --tail=100
```

## Typical Workflows

### 1. Model Training Pipeline (Airflow → MLflow)

```bash
# 1. Access Airflow UI
kubectl port-forward -n mediwatch svc/airflow-webserver-service 8080:8080

# 2. Copy DAG to Airflow
kubectl cp orchestration/airflow/dags/mediwatch_pipeline.py \
  mediwatch/airflow-webserver-<pod-id>:/opt/airflow/dags/

# 3. Trigger DAG from UI or CLI
kubectl exec -n mediwatch airflow-webserver-<pod-id> -- \
  airflow dags trigger mediwatch_training_pipeline

# 4. Monitor in MLflow
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000
# Visit http://localhost:5000
```

### 2. Model Deployment

```bash
# 1. Register model in MLflow (via UI or API)
# 2. Update deployment with new model version
# 3. Trigger Jenkins build with new version
# 4. API automatically pulls new model from MLflow
```

### 3. Monitor Model Performance (Evidently)

```bash
# 1. Generate monitoring report
python monitoring/evidently/generate_report.py

# 2. Upload to Evidently service
kubectl port-forward -n mediwatch svc/evidently-service 8001:8000

curl -X POST http://localhost:8001/upload-report \
  -F "file=@monitoring/evidently/data_drift_report.html"

# 3. View reports
curl http://localhost:8001/reports
open http://localhost:8001/reports/data_drift_report.html
```

## Scaling

### Manual Scaling

```bash
# Scale API replicas
kubectl scale deployment mediwatch-api -n mediwatch --replicas=5

# Scale is also automatic via HPA (2-10 replicas based on CPU/memory)
```

### Resource Limits

Current configuration:

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| API | 500m | 2000m | 1Gi | 4Gi |
| MLflow | 1000m | 4000m | 2Gi | 8Gi |
| Airflow Webserver | 500m | 2000m | 1Gi | 4Gi |
| Airflow Scheduler | 500m | 2000m | 1Gi | 4Gi |
| PostgreSQL | 250m | 1000m | 512Mi | 2Gi |
| Evidently | 250m | 1000m | 512Mi | 2Gi |

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -n mediwatch <pod-name>

# Common issues:
# 1. PVC not bound - check storage class
kubectl get pvc -n mediwatch

# 2. Image pull errors - verify image exists
docker images | grep mediwatch-api

# 3. Resource constraints - check node capacity
kubectl top nodes
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n mediwatch

# Verify LoadBalancer
kubectl get svc -n mediwatch mediwatch-api-service

# Test from within cluster
kubectl run -n mediwatch test-pod --rm -i --tty --image=curlimages/curl -- sh
# Then: curl http://mediwatch-api-service/health
```

### Airflow Database Issues

```bash
# Reinitialize Airflow DB
kubectl exec -n mediwatch airflow-webserver-<pod-id> -- airflow db reset

# Recreate admin user
kubectl exec -n mediwatch airflow-webserver-<pod-id> -- \
  airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@mediwatch.com
```

### Storage Full

```bash
# Check PVC usage
kubectl exec -n mediwatch <pod-name> -- df -h

# Expand PVC (if supported by storage class)
kubectl edit pvc -n mediwatch <pvc-name>
# Increase spec.resources.requests.storage

# Clean old data
kubectl exec -n mediwatch <pod-name> -- rm -rf /path/to/old/data
```

## Cleanup

### Delete Everything

```bash
# Delete namespace (removes all resources)
kubectl delete namespace mediwatch

# PVCs are deleted with namespace
# To keep data, backup PVCs first:
kubectl get pvc -n mediwatch -o yaml > mediwatch-pvcs-backup.yaml
```

### Selective Cleanup

```bash
# Delete specific component
kubectl delete deployment airflow-webserver -n mediwatch
kubectl delete deployment airflow-scheduler -n mediwatch
kubectl delete deployment airflow-postgres -n mediwatch

# Delete all Airflow resources
kubectl delete -f ci-cd/kubernetes/airflow/

# Clean unused PVCs
kubectl delete pvc -n mediwatch <unused-pvc-name>
```

## Security Considerations

### Production Recommendations

1. **Secrets Management**
   ```bash
   # Use Kubernetes secrets for sensitive data
   kubectl create secret generic airflow-secrets \
     --from-literal=postgres-password=<secure-password> \
     --from-literal=fernet-key=<generated-key> \
     -n mediwatch
   ```

2. **Network Policies**
   - Restrict pod-to-pod communication
   - Use ingress controllers for external access
   - Enable TLS for all services

3. **RBAC**
   ```bash
   # Create service accounts with limited permissions
   kubectl create serviceaccount mediwatch-api -n mediwatch
   kubectl create role api-role --verb=get,list --resource=pods -n mediwatch
   kubectl create rolebinding api-binding --role=api-role --serviceaccount=mediwatch:mediwatch-api -n mediwatch
   ```

4. **Resource Quotas**
   ```yaml
   apiVersion: v1
   kind: ResourceQuota
   metadata:
     name: mediwatch-quota
     namespace: mediwatch
   spec:
     hard:
       requests.cpu: "10"
       requests.memory: 20Gi
       persistentvolumeclaims: "10"
   ```

## Backup & Recovery

### Backup Strategy

```bash
# 1. Backup PVCs
for pvc in $(kubectl get pvc -n mediwatch -o name); do
  kubectl get $pvc -n mediwatch -o yaml > backup-$(basename $pvc).yaml
done

# 2. Backup configurations
kubectl get all,cm,secret,pvc -n mediwatch -o yaml > mediwatch-backup.yaml

# 3. Backup MLflow data
kubectl cp mediwatch/mlflow-<pod-id>:/mlflow ./mlflow-backup

# 4. Backup Airflow DAGs
kubectl cp mediwatch/airflow-webserver-<pod-id>:/opt/airflow/dags ./dags-backup
```

### Restore

```bash
# 1. Recreate namespace and resources
kubectl apply -f mediwatch-backup.yaml

# 2. Restore MLflow data
kubectl cp ./mlflow-backup mediwatch/mlflow-<pod-id>:/mlflow

# 3. Restore Airflow DAGs
kubectl cp ./dags-backup mediwatch/airflow-webserver-<pod-id>:/opt/airflow/dags
```

## Performance Tuning

### Optimize for Production

1. **Enable persistent connections**
   - Configure connection pooling for PostgreSQL
   - Use Redis for Airflow Celery executor (if scaling)

2. **Resource allocation**
   - Monitor actual usage: `kubectl top pods -n mediwatch`
   - Adjust requests/limits based on metrics
   - Consider node affinity for co-location

3. **Storage optimization**
   - Use SSD-backed storage for databases
   - Enable compression for MLflow artifacts
   - Implement log rotation for Airflow

## Integration with CI/CD

The complete stack is automatically deployed via Jenkins:

```groovy
// Jenkinsfile stage
stage('Deploy to Kubernetes') {
    when {
        expression { env.DEPLOY_MODE == 'kubernetes' }
    }
    steps {
        sh './ci-cd/kubernetes/deploy.sh ${IMAGE_TAG}'
    }
}
```

## Next Steps

1. **Configure Airflow DAGs** for automated training
2. **Set up Evidently dashboards** for continuous monitoring
3. **Integrate with external model registry** (e.g., AWS S3, Azure Blob)
4. **Enable monitoring** (Prometheus + Grafana)
5. **Set up alerts** for model degradation

## Support

For issues or questions:
- Check logs: `kubectl logs -n mediwatch <pod-name>`
- Describe resources: `kubectl describe <resource> -n mediwatch`
- Review GitHub issues: https://github.com/mykh74/mediwatch/issues
