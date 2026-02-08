# Drift Detection - Quick Reference

## 🎯 Quick Start

### Run Drift Detection Locally
```bash
./scripts/test_drift_detection.sh
```

### View Latest Report
```bash
open monitoring/reports/drift_report_latest.html
```

### Check Drift Metrics
```bash
cat monitoring/reports/drift_metrics_latest.json | jq
```

## 🔧 Configuration

### Drift Thresholds
File: `monitoring/drift_config.yaml`

```yaml
thresholds:
  max_drift_share: 0.30          # 30% features can drift
  max_missing_values: 1000       # Max missing values
  feature_drift_threshold: 0.1   # p-value threshold
```

### Alert Settings
```yaml
alerts:
  fail_on_severe_drift: false    # Don't block deployment
  notify_on_drift: true          # Log warnings
```

## 📊 Pipeline Integration

### Task Flow
```
train_model → evaluate_model → detect_drift → update_api → report
```

### Trigger Pipeline
```bash
# Via Airflow UI
http://localhost:8080 → DAGs → mediwatch_ml_pipeline_enhanced → Trigger

# Via CLI
kubectl exec -n mediwatch -it airflow-xxx -- \
  airflow dags trigger mediwatch_ml_pipeline_enhanced
```

### Monitor Drift Task
```bash
# Get drift detection pod
kubectl get pods -n mediwatch | grep drift

# View logs
kubectl logs -n mediwatch mediwatch-drift-detection-xxx -f
```

## 📈 MLflow Integration

### Access MLflow UI
```bash
# Ensure port forwarding is active
kubectl port-forward -n mediwatch svc/mlflow-service 5000:5000

# Open browser
open http://localhost:5000
```

### View Drift Experiments
```
MLflow UI → Experiments → mediwatch_drift_detection
```

### Key Metrics
- `dataset_drift`: 0 (no drift) or 1 (drift detected)
- `drift_share`: Proportion of drifted features (0.0 - 1.0)
- `num_drifted_features`: Count of drifted features
- `missing_values`: Count of missing values

## 🐳 Docker Build

### Build Image with Evidently
```bash
cd /Users/michaelkuzmyn/projects/ik/MediWatch
docker build -t mediwatch-api:latest ./api
```

### Verify Installation
```bash
docker run --rm mediwatch-api:latest pip list | grep evidently
docker run --rm mediwatch-api:latest ls /opt/scripts/detect_drift.py
```

## 🔍 Troubleshooting

### Check Data Access
```bash
kubectl exec -n mediwatch mediwatch-api-xxx -- ls -la /data/processed/
```

### Test MLflow Connection
```bash
kubectl exec -n mediwatch mediwatch-api-xxx -- \
  curl http://mlflow-service.mediwatch.svc.cluster.local:5000/health
```

### View Drift Reports Directory
```bash
kubectl exec -n mediwatch mediwatch-api-xxx -- ls -la /models/drift_reports/
```

## 📝 Output Files

### Location
```
/models/drift_reports/
├── drift_report_latest.html          # Symlink to latest HTML
├── drift_metrics_latest.json         # Symlink to latest JSON
├── drift_report_20260205_103000.html # Timestamped HTML
└── drift_metrics_20260205_103000.json # Timestamped JSON
```

### Example Metrics JSON
```json
{
  "dataset_drift_detected": false,
  "drift_share": 0.15,
  "num_drifted_features": 3,
  "drifted_features": ["num_medications", "time_in_hospital"],
  "missing_values": 42,
  "has_issues": false,
  "message": "✅ No significant drift detected"
}
```

## 🚨 Drift Indicators

### ✅ Healthy
```
Dataset drift: False
Drift share: 15% (threshold: 30%)
Drifted features: 2
```

### ⚠️ Warning
```
Dataset drift: True
Drift share: 35% (exceeds 30% threshold)
Drifted features: 7
```

### 🔴 Severe (If Enabled)
```
Dataset drift: True
Drift share: 60% (critical level)
Drifted features: 15
Action: Pipeline blocked
```

## 🎛️ Environment Variables

```bash
# Reference data (training baseline)
export REFERENCE_DATA_PATH="/data/processed/train.csv"

# Current data (to check for drift)
export CURRENT_DATA_PATH="/data/processed/test.csv"

# Target column name
export TARGET_COLUMN="readmitted"

# Output directory
export DRIFT_OUTPUT_DIR="/models/drift_reports"

# MLflow connection
export MLFLOW_TRACKING_URI="http://mlflow-service:5000"
```

## 📦 Required Dependencies

### Python Packages
```
evidently>=0.4.23
pandas>=2.0
numpy>=1.24
mlflow>=2.9
```

### System
```
Python 3.11+
Docker
Kubernetes
```

## 🔗 Key Files

| File | Purpose |
|------|---------|
| `scripts/detect_drift.py` | Main drift detection script |
| `scripts/test_drift_detection.sh` | Local test script |
| `monitoring/drift_config.yaml` | Configuration |
| `orchestration/airflow/dags/mediwatch_pipeline_enhanced.py` | Pipeline DAG |
| `docs/DRIFT_DETECTION.md` | Full documentation |

## 📖 Further Reading

- Full documentation: [docs/DRIFT_DETECTION.md](DRIFT_DETECTION.md)
- Evidently AI: https://docs.evidentlyai.com/
- MLflow: https://mlflow.org/docs/

## 💡 Tips

1. **Start with conservative thresholds** (30% drift share)
2. **Review HTML reports** for visual insights
3. **Track drift trends** in MLflow over time
4. **Update reference data** periodically (quarterly)
5. **Monitor drifted features** - same features drifting repeatedly?
