# MediWatch Deployment Guide

Complete guide for deploying the MediWatch patient readmission prediction system.

## Table of Contents

1. [FastAPI Deployment](#fastapi-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Monitoring Setup](#monitoring-setup)
5. [Airflow Orchestration](#airflow-orchestration)
6. [Production Considerations](#production-considerations)

---

## FastAPI Deployment

### Local Development

#### 1. Start MLflow Server

```bash
# Terminal 1: Start MLflow
python scripts/setup_mlflow.py --action start

# Or manually (using virtual environment)
./.venv/bin/mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns

# Or run in background
nohup ./.venv/bin/mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns > mlflow.log 2>&1 &
```

#### 2. Set Environment Variables

```bash
export MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
export MODEL_NAME="mediwatch_readmission_classifier"
export MODEL_STAGE="Production"
export PREPROCESSING_ARTIFACTS_PATH="data/processed/preprocessing_artifacts.pkl"
```

#### 3. Start FastAPI Server

```bash
# Development mode (auto-reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python api/main.py
```

#### 4. Access API

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/model/info` | GET | Model information |
| `/api/v1/predict` | POST | Single prediction |
| `/api/v1/predict/batch` | POST | Batch prediction |
| `/predict` | POST | Legacy prediction |

### Example API Usage

#### Single Prediction

```python
import requests

url = "http://localhost:8000/api/v1/predict"

data = {
    "features": {
        "race": "Caucasian",
        "gender": "Female",
        "age": "[50-60)",
        "admission_type_id": 1,
        "discharge_disposition_id": 1,
        "admission_source_id": 7,
        "time_in_hospital": 3,
        "num_lab_procedures": 41,
        "num_procedures": 0,
        "num_medications": 10,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 0,
        "diag_1": "250.83",
        "diag_2": "250",
        "diag_3": "255",
        "number_diagnoses": 9,
        "max_glu_serum": "None",
        "A1Cresult": "None",
        "metformin": "No",
        "insulin": "Steady",
        "change": "No",
        "diabetesMed": "Yes"
    }
}

response = requests.post(url, json=data)
print(response.json())
# Output: {"prediction": 1, "probability": 0.75, "risk_level": "High", "model_version": "1"}
```

#### Batch Prediction

```python
url = "http://localhost:8000/api/v1/predict/batch"

data = {
    "patients": [
        {...patient1_features...},
        {...patient2_features...},
        {...patient3_features...}
    ]
}

response = requests.post(url, json=data)
print(response.json())
```

---

## Docker Deployment

### Build Docker Image

```bash
# Build image
docker build -t mediwatch-api:latest -f api/Dockerfile .

# Verify image
docker images | grep mediwatch-api
```

### Run Container Locally

```bash
# Run with environment variables
docker run -p 8000:8000 \
  -e MLFLOW_TRACKING_URI="http://host.docker.internal:5000" \
  -e MODEL_NAME="mediwatch_readmission_classifier" \
  -e MODEL_STAGE="Production" \
  -v "$(pwd)/data:/app/data" \
  mediwatch-api:latest

# Run in detached mode
docker run -d -p 8000:8000 --name mediwatch-api mediwatch-api:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mlflow:
    image: python:3.11-slim
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlruns
    command: >
      bash -c "pip install mlflow &&
               mlflow server --host 0.0.0.0 --port 5000
               --backend-store-uri sqlite:///mlruns/mlflow.db
               --default-artifact-root /mlruns"
    networks:
      - mediwatch-network

  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - MODEL_NAME=mediwatch_readmission_classifier
      - MODEL_STAGE=Production
    volumes:
      - ./data:/app/data
    depends_on:
      - mlflow
    networks:
      - mediwatch-network

networks:
  mediwatch-network:
    driver: bridge
```

Run with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (minikube, GKE, EKS, AKS)
- kubectl installed and configured
- Docker images pushed to registry

### 1. Push Images to Registry

```bash
# Tag images
docker tag mediwatch-api:latest your-registry.com/mediwatch-api:latest

# Push to registry
docker push your-registry.com/mediwatch-api:latest
```

### 2. Create Kubernetes Manifests

**mlflow-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlflow
  template:
    metadata:
      labels:
        app: mlflow
    spec:
      containers:
      - name: mlflow
        image: python:3.11-slim
        ports:
        - containerPort: 5000
        command: ["/bin/bash"]
        args:
          - -c
          - |
            pip install mlflow &&
            mlflow server --host 0.0.0.0 --port 5000 \
              --backend-store-uri sqlite:///mlruns/mlflow.db \
              --default-artifact-root /mlruns
        volumeMounts:
        - name: mlflow-data
          mountPath: /mlruns
      volumes:
      - name: mlflow-data
        persistentVolumeClaim:
          claimName: mlflow-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-service
spec:
  selector:
    app: mlflow
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP
```

**api-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mediwatch-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mediwatch-api
  template:
    metadata:
      labels:
        app: mediwatch-api
    spec:
      containers:
      - name: api
        image: your-registry.com/mediwatch-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow-service:5000"
        - name: MODEL_NAME
          value: "mediwatch_readmission_classifier"
        - name: MODEL_STAGE
          value: "Production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mediwatch-api-service
spec:
  selector:
    app: mediwatch-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

**persistent-volume.yaml:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mlflow-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 3. Deploy to Kubernetes

```bash
# Create persistent volume
kubectl apply -f persistent-volume.yaml

# Deploy MLflow
kubectl apply -f mlflow-deployment.yaml

# Deploy API
kubectl apply -f api-deployment.yaml

# Check deployments
kubectl get deployments
kubectl get pods
kubectl get services

# Get external IP
kubectl get service mediwatch-api-service
```

### 4. Access API

```bash
# Get service URL
kubectl get service mediwatch-api-service

# Test API
curl http://<EXTERNAL-IP>/health
```

---

## Monitoring Setup

### 1. Evidently Reports

Generate monitoring reports:

```bash
# Run monitoring report generation
python monitoring/evidently/generate_report.py
```

View reports in `monitoring/reports/` directory.

### 2. Scheduled Monitoring

Create cron job for regular monitoring:

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/MediWatch && python monitoring/evidently/generate_report.py >> logs/monitoring.log 2>&1
```

### 3. Prometheus & Grafana (Optional)

Add Prometheus metrics endpoint to FastAPI:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Add metrics
prediction_counter = Counter('predictions_total', 'Total predictions')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## Airflow Orchestration

### 1. Install Airflow

```bash
# Install Airflow
pip install apache-airflow apache-airflow-providers-docker

# Or use Docker
docker pull apache/airflow:latest
```

### 2. Initialize Airflow

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
    --email admin@mediwatch.com \
    --password admin
```

### 3. Configure Airflow

Copy DAG to Airflow:

```bash
# Copy DAG
cp orchestration/airflow/dags/mediwatch_pipeline.py $AIRFLOW_HOME/dags/

# Update Airflow configuration
# Edit $AIRFLOW_HOME/airflow.cfg:
# dags_folder = /path/to/MediWatch/orchestration/airflow/dags
```

### 4. Start Airflow

```bash
# Start webserver
airflow webserver --port 8080

# Start scheduler (in another terminal)
airflow scheduler
```

### 5. Access Airflow UI

Open http://localhost:8080

- **Username**: admin
- **Password**: admin

### 6. Trigger DAG

```bash
# Trigger manually
airflow dags trigger mediwatch_ml_pipeline

# Or from UI: Toggle DAG to "On" and click "Trigger DAG"
```

---

## Production Considerations

### Security

1. **API Authentication**
   - Add API key authentication
   - Use OAuth2 for user authentication
   - Implement rate limiting

2. **Model Security**
   - Encrypt model artifacts
   - Secure MLflow tracking server
   - Use HTTPS for all communications

3. **Data Privacy**
   - Anonymize patient data
   - Implement HIPAA compliance
   - Audit access logs

### Performance

1. **Caching**
   - Cache preprocessing artifacts
   - Use Redis for prediction caching
   - Implement model version caching

2. **Load Balancing**
   - Use multiple API replicas
   - Implement horizontal pod autoscaling
   - Add CDN for static assets

3. **Optimization**
   - Use async prediction endpoints
   - Batch predictions when possible
   - Optimize model serialization

### Monitoring & Alerting

1. **Application Monitoring**
   - Set up logging aggregation (ELK stack)
   - Monitor API latency and throughput
   - Track error rates

2. **ML Monitoring**
   - Monitor prediction distributions
   - Track data drift metrics
   - Alert on performance degradation

3. **Infrastructure Monitoring**
   - CPU/Memory usage
   - Disk space
   - Network traffic

### Disaster Recovery

1. **Backups**
   - Regular model backups
   - Database backups
   - Configuration backups

2. **High Availability**
   - Multi-region deployment
   - Database replication
   - Automated failover

### CI/CD Pipeline

1. **Automated Testing**
   - Unit tests for all modules
   - Integration tests for API
   - Model performance tests

2. **Deployment Pipeline**
   - Automated Docker builds
   - Kubernetes rolling updates
   - Blue-green deployments

3. **Model Versioning**
   - Semantic versioning for models
   - A/B testing framework
   - Rollback capabilities

---

## Deployment Checklist

- [ ] MLflow server running and accessible
- [ ] Model registered in MLflow registry
- [ ] Model promoted to Production stage
- [ ] Preprocessing artifacts available
- [ ] API tested locally
- [ ] Docker image built and tested
- [ ] Environment variables configured
- [ ] Kubernetes cluster ready (if applicable)
- [ ] Monitoring dashboards set up
- [ ] Airflow DAG configured
- [ ] Logging configured
- [ ] Backups configured
- [ ] Security measures implemented
- [ ] Documentation complete
- [ ] Team trained on operations

---

## Troubleshooting

### API won't start

```bash
# Check MLflow connection
curl http://localhost:5000

# Check model exists
python -c "import mlflow; mlflow.set_tracking_uri('http://localhost:5000'); print(mlflow.search_registered_models())"

# Check preprocessing artifacts
ls -la data/processed/preprocessing_artifacts.pkl
```

### Predictions failing

```bash
# Check model loaded
curl http://localhost:8000/health

# Check model info
curl http://localhost:8000/model/info

# Check logs
docker logs mediwatch-api
```

### Kubernetes pod not starting

```bash
# Describe pod
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)

---

**MediWatch** - Production ML Deployment 🚀
