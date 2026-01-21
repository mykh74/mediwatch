# MediWatch Kubernetes Deployment - Quick Reference

## 🚀 Deploy to Kubernetes via Jenkins

### Option 1: Jenkins UI (Recommended)

1. **Open Jenkins**: http://localhost:8080/job/mediwatch-ci-cd/
2. **Click**: "Build with Parameters"
3. **Set Parameters**:
   - `DEPLOY_MODE`: Select **kubernetes**
   - `RUN_TESTS`: ✅ true
   - `FORCE_REBUILD`: ☐ false (unless needed)
   - `CUSTOM_TAG`: latest (or specific version)
4. **Click**: "Build"

### Option 2: Jenkins CLI

```bash
# Trigger Jenkins build with Kubernetes deployment
curl -X POST http://localhost:8080/job/mediwatch-ci-cd/buildWithParameters \
  --user admin:admin \
  --data DEPLOY_MODE=kubernetes \
  --data RUN_TESTS=true
```

---

## 📦 Manual Kubernetes Deployment

### Prerequisites

```bash
# 1. Verify kubectl is configured
kubectl cluster-info
kubectl get nodes

# 2. Build Docker image (if not done by Jenkins)
docker build -t localhost/mediwatch-api:v1.0.0 -f api/Dockerfile .
```

### Deploy Everything

```bash
# Navigate to Kubernetes directory
cd ci-cd/kubernetes

# Run deployment script
./deploy.sh v1.0.0

# Or use latest tag
./deploy.sh latest
```

### Deploy Step by Step

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Create storage
kubectl apply -f storage/pvc.yaml

# 3. Create ConfigMap
kubectl apply -f configmap.yaml

# 4. Deploy MLflow
kubectl apply -f mlflow/deployment.yaml

# 5. Deploy API
kubectl apply -f api/deployment.yaml
kubectl apply -f api/service.yaml
kubectl apply -f api/hpa.yaml

# 6. Check status
kubectl get all -n mediwatch
```

---

## 🔍 Monitoring & Verification

### Check Deployment Status

```bash
# All resources
kubectl get all -n mediwatch

# Pods with detailed status
kubectl get pods -n mediwatch -o wide

# Services
kubectl get svc -n mediwatch

# HPA status
kubectl get hpa -n mediwatch
```

### View Logs

```bash
# API logs (real-time)
kubectl logs -f deployment/mediwatch-api -n mediwatch

# MLflow logs
kubectl logs -f deployment/mlflow -n mediwatch

# Last 100 lines
kubectl logs --tail=100 deployment/mediwatch-api -n mediwatch
```

### Check Events

```bash
# Recent events
kubectl get events -n mediwatch --sort-by='.lastTimestamp' | head -20

# Describe specific resource
kubectl describe deployment mediwatch-api -n mediwatch
kubectl describe pod <pod-name> -n mediwatch
```

---

## 🌐 Access Services

### Get Service URL

```bash
# Get LoadBalancer external IP/hostname
kubectl get svc mediwatch-api-service -n mediwatch

# Extract IP
EXTERNAL_IP=$(kubectl get svc mediwatch-api-service -n mediwatch \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "API URL: http://$EXTERNAL_IP"
```

### Port-Forward (for local testing)

```bash
# API
kubectl port-forward -n mediwatch svc/mediwatch-api-service 8000:80

# MLflow
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000

# Access in browser:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - MLflow: http://localhost:5000
```

### Test Endpoints

```bash
# Health check
curl http://$EXTERNAL_IP/health

# Model info
curl http://$EXTERNAL_IP/model/info

# Prediction (example)
curl -X POST http://$EXTERNAL_IP/predict \
  -H "Content-Type: application/json" \
  -d '{
    "race": "Caucasian",
    "gender": "Female",
    "age": "[50-60)",
    "time_in_hospital": 3,
    "num_lab_procedures": 45,
    "num_procedures": 2,
    "num_medications": 15,
    "number_diagnoses": 7,
    "max_glu_serum": "None",
    "A1Cresult": ">7",
    "change": "Ch",
    "diabetesMed": "Yes"
  }'
```

---

## 🔄 Updates & Rollouts

### Update Image

```bash
# Update to new version
kubectl set image deployment/mediwatch-api \
  api=localhost/mediwatch-api:v1.1.0 \
  -n mediwatch

# Watch rollout
kubectl rollout status deployment/mediwatch-api -n mediwatch

# Check rollout history
kubectl rollout history deployment/mediwatch-api -n mediwatch
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/mediwatch-api -n mediwatch

# Rollback to specific revision
kubectl rollout undo deployment/mediwatch-api \
  --to-revision=2 \
  -n mediwatch
```

### Restart Deployment

```bash
# Restart without changing image (e.g., after ConfigMap update)
kubectl rollout restart deployment/mediwatch-api -n mediwatch
```

---

## 📊 Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment/mediwatch-api --replicas=5 -n mediwatch

# Verify
kubectl get deployment mediwatch-api -n mediwatch
```

### Auto-Scaling (HPA)

```bash
# View current HPA status
kubectl get hpa mediwatch-api-hpa -n mediwatch

# Describe HPA (shows scaling events)
kubectl describe hpa mediwatch-api-hpa -n mediwatch

# Edit HPA (change min/max replicas or thresholds)
kubectl edit hpa mediwatch-api-hpa -n mediwatch
```

---

## 🐛 Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n mediwatch

# Describe pod for errors
kubectl describe pod <pod-name> -n mediwatch

# Check logs
kubectl logs <pod-name> -n mediwatch

# Check previous logs (if pod restarted)
kubectl logs <pod-name> -n mediwatch --previous
```

### Image Pull Errors

```bash
# For local images (minikube)
eval $(minikube docker-env)
docker images | grep mediwatch

# Rebuild image in minikube
docker build -t localhost/mediwatch-api:latest -f api/Dockerfile .
```

### Service Not Accessible

```bash
# Check service
kubectl get svc mediwatch-api-service -n mediwatch

# Check endpoints (should show pod IPs)
kubectl get endpoints mediwatch-api-service -n mediwatch

# If no endpoints, check pod selector
kubectl get pods -n mediwatch -l app=mediwatch-api
```

### Execute Commands in Pod

```bash
# Get shell in pod
kubectl exec -it deployment/mediwatch-api -n mediwatch -- /bin/bash

# Run single command
kubectl exec deployment/mediwatch-api -n mediwatch -- curl http://localhost:8000/health
```

---

## 🗑️ Cleanup

### Delete Everything

```bash
# Delete namespace (removes all resources)
kubectl delete namespace mediwatch
```

### Delete Specific Resources

```bash
# Delete API deployment
kubectl delete deployment mediwatch-api -n mediwatch

# Delete service
kubectl delete svc mediwatch-api-service -n mediwatch

# Delete all with label
kubectl delete all -l app=mediwatch-api -n mediwatch
```

---

## 📝 Configuration Changes

### Update Environment Variables

```bash
# Edit ConfigMap
kubectl edit configmap mediwatch-config -n mediwatch

# Or apply updated file
kubectl apply -f configmap.yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/mediwatch-api -n mediwatch
```

### Update Resource Limits

```bash
# Edit deployment directly
kubectl edit deployment mediwatch-api -n mediwatch

# Or update deployment.yaml and apply
kubectl apply -f api/deployment.yaml
```

---

## 🔐 Security (Production)

### Create Secrets

```bash
# Create secret for sensitive data
kubectl create secret generic mediwatch-secrets \
  --from-literal=MLFLOW_TOKEN=your_token_here \
  --from-literal=API_KEY=your_api_key \
  -n mediwatch

# Verify
kubectl get secrets -n mediwatch
```

### Use Secrets in Deployment

Add to `api/deployment.yaml`:
```yaml
env:
- name: API_KEY
  valueFrom:
    secretKeyRef:
      name: mediwatch-secrets
      key: API_KEY
```

---

## 📞 Quick Commands Cheat Sheet

```bash
# Status
kubectl get all -n mediwatch

# Logs (real-time)
kubectl logs -f deployment/mediwatch-api -n mediwatch

# Shell access
kubectl exec -it deployment/mediwatch-api -n mediwatch -- /bin/bash

# Port-forward
kubectl port-forward -n mediwatch svc/mediwatch-api-service 8000:80

# Restart
kubectl rollout restart deployment/mediwatch-api -n mediwatch

# Scale
kubectl scale deployment/mediwatch-api --replicas=5 -n mediwatch

# Update image
kubectl set image deployment/mediwatch-api api=localhost/mediwatch-api:v2 -n mediwatch

# Rollback
kubectl rollout undo deployment/mediwatch-api -n mediwatch

# Delete
kubectl delete namespace mediwatch
```

---

## 🆘 Getting Help

```bash
# kubectl help
kubectl --help
kubectl get --help

# Kubernetes dashboard (if installed)
kubectl proxy
# Then open: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/

# Check cluster info
kubectl cluster-info
kubectl version
```

---

**For detailed information**, see the complete [README.md](./README.md) in this directory.
