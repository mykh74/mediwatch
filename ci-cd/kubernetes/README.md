# MediWatch Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the complete MediWatch ML stack.

## 📁 Structure

```
ci-cd/kubernetes/
├── namespace.yaml              # MediWatch namespace
├── configmap.yaml             # Environment configuration
├── deploy.sh                  # Main deployment script
├── api/
│   ├── deployment.yaml        # API deployment with replicas
│   ├── service.yaml           # LoadBalancer service
│   └── hpa.yaml              # Horizontal Pod Autoscaler
├── mlflow/
│   └── deployment.yaml        # MLflow tracking server
└── storage/
    └── pvc.yaml              # Persistent Volume Claims
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes cluster** (minikube, EKS, GKE, AKS, or local)
2. **kubectl** configured and authenticated
3. **Docker image** built and available

### Manual Deployment

```bash
# Deploy everything
cd ci-cd/kubernetes
chmod +x deploy.sh
./deploy.sh <image-tag>

# Example with specific tag
./deploy.sh v1.0.0

# Or use latest
./deploy.sh latest
```

### Via Jenkins

The Kubernetes deployment is integrated into the Jenkins CI/CD pipeline:

1. Go to Jenkins: http://localhost:8080/job/mediwatch-ci-cd/
2. Click "Build with Parameters"
3. Set:
   - `DEPLOY_MODE` = **kubernetes**
   - `RUN_TESTS` = true
   - Other parameters as needed
4. Click "Build"

The pipeline will:
- Build Docker image
- Run tests
- Deploy to Kubernetes
- Run smoke tests
- Report status

## 🔧 Manual kubectl Commands

### Deploy Individual Components

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Create storage
kubectl apply -f storage/pvc.yaml

# 3. Deploy MLflow
kubectl apply -f mlflow/deployment.yaml

# 4. Deploy ConfigMap
kubectl apply -f configmap.yaml

# 5. Deploy API
kubectl apply -f api/deployment.yaml
kubectl apply -f api/service.yaml
kubectl apply -f api/hpa.yaml
```

### Update Deployment with New Image

```bash
# Set new image
kubectl set image deployment/mediwatch-api \
  api=localhost/mediwatch-api:v1.2.3 \
  -n mediwatch

# Check rollout status
kubectl rollout status deployment/mediwatch-api -n mediwatch

# View history
kubectl rollout history deployment/mediwatch-api -n mediwatch

# Rollback if needed
kubectl rollout undo deployment/mediwatch-api -n mediwatch
```

## 📊 Monitoring & Management

### Check Status

```bash
# All resources
kubectl get all -n mediwatch

# Pods
kubectl get pods -n mediwatch

# Services
kubectl get svc -n mediwatch

# HPA status
kubectl get hpa -n mediwatch

# Events
kubectl get events -n mediwatch --sort-by='.lastTimestamp'
```

### View Logs

```bash
# API logs (all replicas)
kubectl logs -f deployment/mediwatch-api -n mediwatch

# Specific pod
kubectl logs -f <pod-name> -n mediwatch

# Previous pod logs
kubectl logs <pod-name> -n mediwatch --previous

# MLflow logs
kubectl logs -f deployment/mlflow -n mediwatch
```

### Access Services

```bash
# Get LoadBalancer IP/hostname
kubectl get svc mediwatch-api-service -n mediwatch

# Port-forward for local access
kubectl port-forward -n mediwatch svc/mediwatch-api-service 8000:80
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000

# Then access:
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MLflow: http://localhost:5000
```

### Execute Commands in Pods

```bash
# Shell into API pod
kubectl exec -it deployment/mediwatch-api -n mediwatch -- /bin/bash

# Run health check
kubectl exec deployment/mediwatch-api -n mediwatch -- \
  curl -f http://localhost:8000/health
```

## 🔄 Scaling

### Manual Scaling

```bash
# Scale API replicas
kubectl scale deployment/mediwatch-api --replicas=5 -n mediwatch

# Check scaling status
kubectl get deployment mediwatch-api -n mediwatch
kubectl get pods -n mediwatch -l app=mediwatch-api
```

### Auto-scaling (HPA)

The HPA is configured to scale between 2-10 replicas based on:
- CPU utilization: 70%
- Memory utilization: 80%

```bash
# View HPA status
kubectl get hpa mediwatch-api-hpa -n mediwatch

# Describe HPA
kubectl describe hpa mediwatch-api-hpa -n mediwatch

# Modify HPA
kubectl edit hpa mediwatch-api-hpa -n mediwatch
```

## 🗑️ Cleanup

### Delete Everything

```bash
# Delete entire namespace (including all resources)
kubectl delete namespace mediwatch

# Or delete individually
kubectl delete -f api/ -n mediwatch
kubectl delete -f mlflow/deployment.yaml -n mediwatch
kubectl delete -f storage/pvc.yaml -n mediwatch
kubectl delete -f configmap.yaml -n mediwatch
kubectl delete -f namespace.yaml
```

### Delete Specific Components

```bash
# Delete API only
kubectl delete deployment mediwatch-api -n mediwatch
kubectl delete svc mediwatch-api-service -n mediwatch
kubectl delete hpa mediwatch-api-hpa -n mediwatch

# Delete MLflow
kubectl delete deployment mlflow -n mediwatch
kubectl delete svc mlflow-service -n mediwatch
```

## ⚙️ Configuration

### Environment Variables

Edit `configmap.yaml` to change:

```yaml
data:
  MLFLOW_TRACKING_URI: "http://mlflow-service:5000"
  MODEL_NAME: "mediwatch_readmission_classifier"
  MODEL_STAGE: "Production"
  LOG_LEVEL: "INFO"
  API_TIMEOUT: "30"
```

Apply changes:
```bash
kubectl apply -f configmap.yaml
kubectl rollout restart deployment/mediwatch-api -n mediwatch
```

### Resource Limits

Edit resource requests/limits in `api/deployment.yaml`:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Replicas

Edit `api/deployment.yaml`:
```yaml
spec:
  replicas: 3  # Change this number
```

## 🔒 Security

### Secrets (TODO)

For production, create secrets:

```bash
# Create generic secret
kubectl create secret generic mediwatch-secrets \
  --from-literal=POSTGRES_PASSWORD=secure_password \
  --from-literal=MLFLOW_TOKEN=mlflow_token \
  -n mediwatch

# Use in deployment
# Add to deployment.yaml under env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: mediwatch-secrets
      key: POSTGRES_PASSWORD
```

### Network Policies (TODO)

Implement network policies to restrict pod-to-pod communication.

## 🧪 Testing Deployment

```bash
# 1. Check all pods are running
kubectl get pods -n mediwatch

# 2. Test API health
EXTERNAL_IP=$(kubectl get svc mediwatch-api-service -n mediwatch -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health

# 3. Test prediction endpoint
curl -X POST http://$EXTERNAL_IP/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json

# 4. Check MLflow
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000 &
curl http://localhost:5000/health
```

## 📈 Production Considerations

### High Availability

1. **Multiple replicas**: Minimum 3 for API
2. **Pod Disruption Budget**: Ensure availability during updates
3. **Multi-zone deployment**: Spread pods across availability zones
4. **Health checks**: Properly configured liveness/readiness probes

### Monitoring

Consider adding:
- Prometheus for metrics collection
- Grafana for dashboards
- ELK stack for log aggregation
- Jaeger for distributed tracing

### Persistence

- Use proper StorageClass for production
- Regular backups of PVCs
- MLflow artifacts to object storage (S3, GCS, Azure Blob)

### CI/CD Integration

Jenkins pipeline automatically:
1. Builds Docker image
2. Runs tests
3. Deploys to Kubernetes
4. Performs smoke tests
5. Rolls back on failure

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [MLflow on Kubernetes](https://mlflow.org/docs/latest/deployment/kubernetes.html)
- [Jenkins Kubernetes Plugin](https://plugins.jenkins.io/kubernetes/)

## 🆘 Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n mediwatch

# Check events
kubectl get events -n mediwatch --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n mediwatch
```

### Image pull errors

```bash
# Check image pull policy
kubectl get deployment mediwatch-api -n mediwatch -o yaml | grep imagePullPolicy

# For local images (minikube):
eval $(minikube docker-env)
docker images | grep mediwatch
```

### Service not accessible

```bash
# Check service
kubectl get svc mediwatch-api-service -n mediwatch

# Check endpoints
kubectl get endpoints mediwatch-api-service -n mediwatch

# Port-forward for debugging
kubectl port-forward -n mediwatch svc/mediwatch-api-service 8000:80
```

### PVC pending

```bash
# Check PVC status
kubectl get pvc -n mediwatch

# Check storage classes
kubectl get sc

# Describe PVC for issues
kubectl describe pvc <pvc-name> -n mediwatch
```
