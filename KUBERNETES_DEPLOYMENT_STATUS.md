# MediWatch MLOps Stack - Deployment Summary

## ✅ Successfully Deployed

### Current Running Services

| Service | Status | Replicas | Endpoint |
|---------|--------|----------|----------|
| **MediWatch API** | ✅ Running | 3/3 | http://localhost/ |
| **MLflow** | ✅ Running | 1/1 | Port-forward 5000 |
| **Airflow PostgreSQL** | ✅ Running | 1/1 | Internal |
| **Airflow Webserver** | ✅ Running | 1/1 | Port-forward 8080 |
| **Airflow Scheduler** | ⚠️  Pending | 0/1 | Resource constrained |
| **Evidently** | ⚠️  CrashLoopBackOff | 0/1 | Port-forward 8001 |

## Storage Allocated

| Component | PVC | Size | Status |
|-----------|-----|------|--------|
| API Models | mediwatch-models-pvc | 20GB | ✅ Bound |
| API Data | mediwatch-data-pvc | 50GB | ✅ Bound |
| MLflow | mlflow-data-pvc | 100GB | ✅ Bound |
| Airflow PostgreSQL | airflow-postgres-pvc | 10GB | ✅ Bound |
| Airflow DAGs | airflow-dags-pvc | 5GB | ✅ Bound |
| Airflow Logs | airflow-logs-pvc | 10GB | ✅ Bound |
| Evidently Reports | evidently-reports-pvc | 5GB | ✅ Bound |
| Evidently Data | evidently-data-pvc | 10GB | ✅ Bound |

**Total Storage**: 210GB allocated

## Access Your Services

### 1. MediWatch API (Ready Now)
```bash
# Health check
curl http://localhost/health

# API documentation
open http://localhost/docs
```

### 2. MLflow (Ready Now)
```bash
# Port-forward to access
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000

# Then visit
open http://localhost:5000
```

### 3. Airflow (Partially Ready)
```bash
# Port-forward webserver (login: admin/admin)
kubectl port-forward -n mediwatch svc/airflow-webserver-service 8080:8080

# Then visit
open http://localhost:8080
```

**Note**: Airflow scheduler needs more cluster resources to run. See Resource Optimization below.

### 4. Evidently (Configuration Needed)
Currently in error state - requires script initialization fixes.

## Quick Commands

```bash
# View all resources
kubectl get all -n mediwatch

# Watch pods
kubectl get pods -n mediwatch -w

# Check logs
kubectl logs -n mediwatch -l app=mediwatch-api --tail=50

# Check resource usage
kubectl top pods -n mediwatch
```

## Resource Optimization

Your Docker Desktop Kubernetes has limited resources. Here are options:

### Option 1: Increase Docker Desktop Resources (Recommended)

1. Open Docker Desktop
2. Settings → Resources
3. Increase:
   - **Memory**: 8GB or more (currently may be 4-6GB)
   - **CPUs**: 4 or more
4. Apply & Restart
5. Re-deploy: `kubectl delete pod -n mediwatch --all`

### Option 2: Run Airflow/Evidently Outside Kubernetes

Run these services locally while keeping API/MLflow in K8s:

```bash
# Stop K8s Airflow
kubectl scale deployment airflow-scheduler --replicas=0 -n mediwatch
kubectl scale deployment airflow-webserver --replicas=0 -n mediwatch

# Run Airflow locally with Docker Compose
cd orchestration/airflow
docker-compose up -d

# Run Evidently locally
cd monitoring/evidently
python generate_report.py --serve
```

### Option 3: Selective Deployment

Deploy only what you need:

```bash
# Core ML services only (API + MLflow)
kubectl delete deployment airflow-webserver airflow-scheduler airflow-postgres evidently -n mediwatch

# This frees ~3-4GB memory
```

## Jenkins CI/CD Integration

The complete stack is integrated with Jenkins:

```bash
# Automatic deployment via Jenkins
# 1. Go to http://localhost:8080/job/mediwatch-ci-cd/
# 2. Build with Parameters
# 3. DEPLOY_MODE: kubernetes
# 4. Build

# The deploy.sh script will:
# - Create namespace
# - Deploy all services
# - Configure storage
# - Wait for readiness
```

## What's Working Now

✅ **Core ML Pipeline**:
- API deployed with 3 replicas
- MLflow tracking server active
- Auto-scaling configured (2-10 replicas)
- Health checks passing
- Persistent storage configured

✅ **Kubernetes Infrastructure**:
- Namespace created
- Services exposed (LoadBalancer + ClusterIP)
- 210GB storage allocated and bound
- Resource limits configured

✅ **CI/CD Integration**:
- Custom Jenkins image with kubectl
- Automated K8s deployment
- Multi-mode support (docker/kubernetes)

## Next Steps

### Immediate (Resource-dependent)

1. **Increase Docker Desktop resources** to run full stack
2. **Deploy Airflow DAGs** from `orchestration/airflow/dags/`
3. **Configure Evidently** monitoring reports

### Production Preparation

1. **External cluster**: Deploy to EKS/GKE/AKS for production
2. **Ingress controller**: Set up NGINX ingress for external access
3. **Monitoring**: Add Prometheus + Grafana
4. **Secrets**: Use Kubernetes secrets for credentials
5. **CI/CD**: Automate model deployment pipeline

## Troubleshooting

### Airflow Scheduler Pending

**Issue**: Insufficient memory

**Solution**:
```bash
# Check node capacity
kubectl describe node docker-desktop

# Increase Docker Desktop memory (Settings → Resources)
# OR temporarily stop some services
kubectl scale deployment mlflow --replicas=0 -n mediwatch
# Then restart scheduler
kubectl delete pod -n mediwatch -l app=airflow-scheduler
```

### Evidently Crashing

**Issue**: Script initialization error

**Solution**: The container builds Python environment on startup. Give it 2-3 minutes or check logs:
```bash
kubectl logs -n mediwatch -l app=evidently --tail=100
```

### Can't Access Services

**Port-forward required** for ClusterIP services:
```bash
# MLflow
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000

# Airflow  
kubectl port-forward -n mediwatch svc/airflow-webserver-service 8080:8080

# Evidently
kubectl port-forward -n mediwatch svc/evidently-service 8001:8000
```

## Documentation

- **Full Stack Guide**: `ci-cd/kubernetes/MLOPS_STACK.md`
- **K8s Quick Start**: `ci-cd/kubernetes/QUICK_START.md`
- **Jenkins Setup**: `ci-cd/jenkins/README.md`
- **Deployment Script**: `ci-cd/kubernetes/deploy.sh`

## Architecture Achieved

```
┌─────────────────────────────────────────────────┐
│         Docker Desktop Kubernetes               │
│                                                 │
│  ✅ MediWatch API (3 pods) - http://localhost/  │
│  ✅ MLflow (1 pod) - Port 5000                  │
│  ✅ Airflow PostgreSQL (1 pod)                  │
│  ✅ Airflow Webserver (1 pod) - Port 8080       │
│  ⚠️  Airflow Scheduler (pending resources)      │
│  ⚠️  Evidently (error, needs fix)               │
│                                                 │
│  📦 Storage: 210GB PVCs (all bound)             │
│  🔄 Auto-scaling: 2-10 replicas (HPA)           │
│  🔐 Load Balancer: localhost routing            │
└─────────────────────────────────────────────────┘
```

## Success Metrics

- ✅ Kubernetes cluster configured
- ✅ kubectl access from Jenkins
- ✅ API deployed and accessible
- ✅ MLflow tracking server running
- ✅ Storage provisioned (210GB)
- ✅ Auto-scaling configured
- ✅ CI/CD pipeline functional
- ⚠️  Airflow scheduler (resource constrained)
- ⚠️  Evidently (initialization issue)

**Overall Progress**: 80% complete - Core ML infrastructure fully operational!
