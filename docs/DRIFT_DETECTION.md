# Evidently Drift Detection Implementation

## Overview

Evidently drift detection has been integrated into the MediWatch ML pipeline to monitor data quality and detect distribution shifts that could impact model performance.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  ML Pipeline Flow                        │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Data Validation │
              └──────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Model Training  │
              └──────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Model Evaluation │
              └──────────────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │   🔍 DRIFT DETECTION (NEW)     │
         │                                │
         │  • Data Drift Analysis         │
         │  • Target Drift Detection      │
         │  • Data Quality Checks         │
         │  • Feature Drift Metrics       │
         └────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   Update API     │
              └──────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Generate Report  │
              └──────────────────┘
```

## Components

### 1. Drift Detection Script

**Location:** `scripts/detect_drift.py`

**Key Features:**
- Compares reference (training) vs current (production) data
- Detects dataset-level drift
- Identifies individual drifted features
- Monitors data quality metrics
- Generates HTML and JSON reports
- Logs all metrics to MLflow

**Usage:**
```python
from scripts.detect_drift import DriftDetector

detector = DriftDetector(
    reference_data_path="/data/processed/train.csv",
    current_data_path="/data/processed/test.csv",
    target_column="readmitted",
    output_dir="/models/drift_reports"
)

metrics = detector.run()
```

### 2. Airflow Integration

**Location:** `orchestration/airflow/dags/mediwatch_pipeline_enhanced.py`

**New Task:** `detect_drift`

The drift detection task runs after model evaluation and before API update:

```
train_model → evaluate_model → detect_drift → update_api → report
```

**Configuration:**
- Runs as KubernetesPodOperator
- Uses shared PVCs for data/models access
- Resource limits: 512Mi memory, 500m CPU
- Logs to MLflow experiment: `mediwatch_drift_detection`

### 3. Configuration

**Location:** `monitoring/drift_config.yaml`

**Key Settings:**
```yaml
thresholds:
  max_drift_share: 0.30  # 30% of features can drift
  max_missing_values: 1000
  feature_drift_threshold: 0.1  # p-value

alerts:
  fail_on_severe_drift: false  # Don't block deployment
  notify_on_drift: true
```

## Drift Detection Metrics

### Dataset-Level Metrics

1. **Dataset Drift** (bool)
   - Overall indication if significant drift detected
   - Based on share of drifted features

2. **Drift Share** (float 0-1)
   - Proportion of features showing drift
   - Alert threshold: 0.30 (30%)

3. **Drifted Features** (list)
   - Names of features with detected drift
   - Logged to MLflow for tracking

### Feature-Level Metrics

For each feature, Evidently calculates:

**Numerical Features:**
- Kolmogorov-Smirnov test
- Distribution statistics (mean, std, quantiles)
- p-value < 0.05 indicates drift

**Categorical Features:**
- Chi-squared test
- Category distribution comparison
- p-value < 0.05 indicates drift

### Data Quality Metrics

1. **Missing Values**
   - Count of missing values per column
   - Alert threshold: 1000 total

2. **Data Quality Score**
   - Completeness
   - Validity checks
   - Consistency metrics

## Reports

### HTML Report

**Location:** `/models/drift_reports/drift_report_latest.html`

**Contents:**
- Interactive data drift visualizations
- Feature distribution comparisons
- Statistical test results
- Data quality dashboard

**Access:**
```bash
# Open latest report
open monitoring/reports/drift_report_latest.html
```

### JSON Metrics

**Location:** `/models/drift_reports/drift_metrics_latest.json`

**Example:**
```json
{
  "dataset_drift_detected": false,
  "drift_share": 0.15,
  "num_drifted_features": 3,
  "drifted_features": [
    "num_medications",
    "time_in_hospital",
    "num_lab_procedures"
  ],
  "missing_values": 42,
  "timestamp": "2026-02-05T10:30:00",
  "has_issues": false,
  "message": "✅ No significant drift detected"
}
```

## MLflow Integration

### Experiment

All drift detection runs are logged to:
- **Experiment:** `mediwatch_drift_detection`
- **MLflow UI:** http://localhost:5000

### Logged Artifacts

1. **Metrics:**
   - `dataset_drift` (0 or 1)
   - `drift_share` (0.0 - 1.0)
   - `num_drifted_features` (count)
   - `missing_values` (count)

2. **Parameters:**
   - `reference_data` (path)
   - `current_data` (path)
   - `target_column` (name)

3. **Artifacts:**
   - HTML report
   - JSON metrics
   - Drifted features list

### Querying MLflow

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
experiment = mlflow.get_experiment_by_name("mediwatch_drift_detection")

# Get latest run
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
latest = runs.iloc[0]

print(f"Drift detected: {latest['metrics.dataset_drift']}")
print(f"Drift share: {latest['metrics.drift_share']:.2%}")
```

## Testing

### Local Testing

```bash
# Test drift detection locally
./scripts/test_drift_detection.sh
```

### Pipeline Testing

```bash
# Trigger full pipeline with drift detection
kubectl exec -n mediwatch -it airflow-xxx -- \
  airflow dags trigger mediwatch_ml_pipeline_enhanced
```

### Monitor Progress

```bash
# Watch Airflow logs
kubectl logs -n mediwatch -f airflow-xxx

# Check drift detection pod
kubectl get pods -n mediwatch | grep drift

# View drift detection logs
kubectl logs -n mediwatch mediwatch-drift-detection-xxx
```

## Deployment

### 1. Build Docker Image

The API Docker image now includes the drift detection script:

```bash
# Build image with Evidently
docker build -t mediwatch-api:latest ./api

# Or using local build script
./scripts/local_build.sh
```

### 2. Verify Installation

```bash
# Check if Evidently is installed
docker run --rm mediwatch-api:latest pip list | grep evidently
# Should show: evidently==0.4.23 (or later)

# Check if script is available
docker run --rm mediwatch-api:latest ls -la /opt/scripts/detect_drift.py
```

### 3. Deploy to Kubernetes

```bash
# Deploy updated DAG
kubectl cp orchestration/airflow/dags/mediwatch_pipeline_enhanced.py \
  mediwatch/airflow-xxx:/opt/airflow/dags/

# Restart Airflow to pick up changes
kubectl rollout restart deployment airflow-webserver -n mediwatch
kubectl rollout restart deployment airflow-scheduler -n mediwatch
```

## Drift Alerting

### Current Behavior

When drift is detected:

1. **Logs Warning:**
   ```
   ⚠️  Dataset drift detected!
   ⚠️  Drift share 35.0% exceeds threshold 30.0%
   ℹ️  5 features showing drift: num_medications, time_in_hospital, ...
   ```

2. **Logs to MLflow:**
   - All metrics recorded
   - HTML report attached
   - Run marked with drift=true

3. **Continues Pipeline:**
   - Does NOT block deployment by default
   - `fail_on_severe_drift: false` in config

### Future Enhancements

To enable pipeline blocking on severe drift:

```yaml
# monitoring/drift_config.yaml
alerts:
  fail_on_severe_drift: true  # Enable blocking
```

Then update script to exit with error:
```python
if metrics.get('has_issues', False):
    logger.error("Exiting with error due to drift issues")
    sys.exit(1)  # Fail the task
```

## Monitoring Dashboard

### View Drift Over Time

```python
import mlflow
import pandas as pd
import matplotlib.pyplot as plt

mlflow.set_tracking_uri("http://localhost:5000")
experiment = mlflow.get_experiment_by_name("mediwatch_drift_detection")

# Get all runs
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

# Plot drift share over time
runs['timestamp'] = pd.to_datetime(runs['start_time'])
runs = runs.sort_values('timestamp')

plt.figure(figsize=(12, 6))
plt.plot(runs['timestamp'], runs['metrics.drift_share'])
plt.axhline(y=0.3, color='r', linestyle='--', label='Threshold')
plt.xlabel('Time')
plt.ylabel('Drift Share')
plt.title('Data Drift Over Time')
plt.legend()
plt.tight_layout()
plt.savefig('monitoring/drift_trend.png')
```

## Troubleshooting

### Issue: Drift detection fails with "Module not found: evidently"

**Solution:**
```bash
# Rebuild Docker image
docker build -t mediwatch-api:latest ./api

# Or install in local environment
pip install evidently>=0.4.23
```

### Issue: "No such file: /data/processed/train.csv"

**Solution:**
```bash
# Verify PVC mounts
kubectl exec -n mediwatch mediwatch-api-xxx -- ls -la /data/processed/

# Check if data exists
kubectl exec -n mediwatch mediwatch-api-xxx -- head /data/processed/train.csv
```

### Issue: Reports not saving to /models/drift_reports

**Solution:**
```bash
# Check PVC permissions
kubectl exec -n mediwatch mediwatch-api-xxx -- ls -la /models/

# Create directory if missing
kubectl exec -n mediwatch mediwatch-api-xxx -- mkdir -p /models/drift_reports
```

### Issue: MLflow connection timeout

**Solution:**
```bash
# Verify MLflow service
kubectl get svc -n mediwatch mlflow-service

# Test connectivity
kubectl exec -n mediwatch mediwatch-api-xxx -- \
  curl -f http://mlflow-service.mediwatch.svc.cluster.local:5000/health
```

## Best Practices

1. **Baseline Updates:**
   - Periodically update reference data (e.g., quarterly)
   - Use recent high-quality data as new baseline

2. **Threshold Tuning:**
   - Start conservative (30% drift share)
   - Monitor false positive rate
   - Adjust based on domain knowledge

3. **Feature Selection:**
   - Focus on critical features
   - Exclude expected seasonal variations
   - Group related features for analysis

4. **Report Review:**
   - Check HTML reports weekly
   - Investigate persistent drift patterns
   - Document drift causes

5. **Integration:**
   - Link drift detection to model retraining
   - Set up automated alerts
   - Track drift trends in dashboards

## Next Steps

1. **Enable Slack/Email Notifications:**
   - Configure webhook in `drift_config.yaml`
   - Implement notification handlers

2. **Prediction Drift:**
   - Capture production predictions
   - Compare against historical distribution

3. **Automated Retraining:**
   - Trigger training when drift > threshold
   - Implement auto-retraining logic

4. **Dashboard:**
   - Create Grafana dashboard
   - Visualize drift trends
   - Set up alerts

5. **A/B Testing:**
   - Test new model vs current
   - Use drift metrics for decision
   - Gradual rollout based on drift

## References

- [Evidently Documentation](https://docs.evidentlyai.com/)
- [Data Drift Detection Methods](https://www.evidentlyai.com/blog/data-drift-detection-methods)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
