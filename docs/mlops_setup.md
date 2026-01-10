# MLOps Setup Guide

## Overview

This guide covers the MLOps infrastructure setup for the MediWatch project, including:
- MLflow for experiment tracking and model registry
- Ray Tune for hyperparameter optimization
- Model training workflow
- Model deployment preparation

## Prerequisites

```bash
# Install all dependencies
pip install -r requirements.txt
```

## MLflow Setup

### 1. Start MLflow Server

**Option A: Using the setup script**
```bash
python scripts/setup_mlflow.py --action start
```

**Option B: Manual start (using virtual environment)**
```bash
# Start server with mlruns.db (latest database)
./.venv/bin/mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns

# Or run in background
nohup ./.venv/bin/mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns > mlflow.log 2>&1 &
```

**Option C: Stop and restart**
```bash
# Kill existing MLflow server
pkill -f "mlflow server"
# Or kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Then start as shown above
```

### 2. Initialize Experiment

```bash
python scripts/setup_mlflow.py --action init --experiment mediwatch-readmission
```

Or programmatically:
```python
from mediwatch.registry.mlflow_registry import setup_mlflow

experiment_id = setup_mlflow(
    tracking_uri="http://127.0.0.1:5000",
    experiment_name="mediwatch-readmission"
)
```

### 3. Access MLflow UI

Open your browser and navigate to: http://127.0.0.1:5000

## Directory Structure

```
MediWatch/
├── mlruns/              # MLflow tracking data
│   ├── mlflow.db       # SQLite backend
│   └── <experiment_id>/ # Experiment artifacts
├── data/
│   ├── processed/      # Preprocessed training data
│   └── models/         # Saved model artifacts
└── notebooks/
    └── 02_model_training.ipynb  # Main training notebook
```

## Model Training Workflow

### 1. Prepare Data

```python
from mediwatch.data.preprocess import PreprocessingArtifacts
import pandas as pd

# Load preprocessed data
train_df = pd.read_csv('data/processed/train.csv')
test_df = pd.read_csv('data/processed/test.csv')

# Load artifacts
artifacts = PreprocessingArtifacts.load('data/processed/preprocessing_artifacts.pkl')

# Separate features and target
target_col = artifacts.metadata['target_col']
X_train = train_df.drop(columns=[target_col])
y_train = train_df[target_col]
X_test = test_df.drop(columns=[target_col])
y_test = test_df[target_col]
```

### 2. Train Baseline Models

```python
from mediwatch.models.train import train_all_baselines

# Train all baseline models
results = train_all_baselines(
    x_train=X_train,
    y_train=y_train,
    use_scaling=True,
    track_mlflow=True,
    experiment_name="mediwatch-readmission"
)
```

Available baseline models:
- `logistic_regression`: L2-regularized logistic regression
- `random_forest`: Random forest classifier with 100 trees
- `gradient_boosting`: Gradient boosting classifier
- `xgboost`: XGBoost classifier (if installed)
- `lightgbm`: LightGBM classifier (if installed)

### 3. Evaluate Models

```python
from mediwatch.models.evaluate import evaluate_model, compare_models, print_evaluation_report

# Evaluate single model
metrics = evaluate_model(
    pipeline=results['random_forest'].pipeline,
    x_test=X_test,
    y_test=y_test,
    track_mlflow=True
)

print_evaluation_report(metrics, "Random Forest")

# Compare all models
pipelines = {name: artifacts.pipeline for name, artifacts in results.items()}
comparison_df = compare_models(
    models=pipelines,
    x_test=X_test,
    y_test=y_test
)
```

### 4. Hyperparameter Optimization with Ray Tune

```python
from mediwatch.models.tune import run_hpo

# Tune single model
hpo_results = run_hpo(
    x_train=X_train,
    y_train=y_train,
    model_name="random_forest",
    num_samples=20,          # Number of trials
    max_concurrent_trials=4,  # Parallel trials
    cv=3,                    # Cross-validation folds
    use_scaling=False,
    mlflow_experiment_name="mediwatch-readmission"
)

print(f"Best config: {hpo_results['best_config']}")
print(f"Best score: {hpo_results['best_score']:.4f}")
```

**Search Spaces:**
- **Logistic Regression**: C, penalty, solver
- **Random Forest**: n_estimators, max_depth, min_samples_split, min_samples_leaf
- **Gradient Boosting**: n_estimators, learning_rate, max_depth, min_samples_split
- **XGBoost**: n_estimators, learning_rate, max_depth, min_child_weight, subsample, colsample_bytree
- **LightGBM**: n_estimators, learning_rate, max_depth, num_leaves, min_child_samples

### 5. Train Final Model with Best Hyperparameters

```python
from mediwatch.models.train import train_model

# Train with optimized hyperparameters
best_model = train_model(
    x_train=X_train,
    y_train=y_train,
    model_name="random_forest",
    model_params=hpo_results['best_config'],
    use_scaling=False,
    track_mlflow=True,
    experiment_name="mediwatch-readmission"
)
```

## MLflow Model Registry

### 1. Select Best Model

```python
from mediwatch.registry.mlflow_registry import get_best_run

# Find best run by metric
best_run = get_best_run(
    experiment_name="mediwatch-readmission",
    metric="test_f1",
    tracking_uri="http://127.0.0.1:5000"
)

print(f"Best run ID: {best_run.info.run_id}")
print(f"Metrics: {best_run.data.metrics}")
```

### 2. Register Model

```python
from mediwatch.registry.mlflow_registry import register_model

# Register model from best run
model_uri = f"runs:/{best_run.info.run_id}/model"

model_version = register_model(
    model_uri=model_uri,
    model_name="mediwatch_readmission_classifier",
    tags={
        "task": "readmission_prediction",
        "framework": "sklearn",
    },
    description="Production model for patient readmission prediction"
)

print(f"Registered model version: {model_version.version}")
```

### 3. Promote to Production

```python
from mediwatch.registry.mlflow_registry import promote_model_to_production

# Promote latest version to production
promote_model_to_production(
    model_name="mediwatch_readmission_classifier",
    tracking_uri="http://127.0.0.1:5000"
)
```

### 4. Load Model for Inference

```python
from mediwatch.registry.mlflow_registry import load_best_model

# Load production model
model = load_best_model(
    model_name="mediwatch_readmission_classifier",
    stage="Production",
    tracking_uri="http://127.0.0.1:5000"
)

# Make predictions
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)
```

## Ray Tune Configuration

### Scheduler Options

**ASHA (Async Successive Halving)**
```python
from ray.tune.schedulers import ASHAScheduler

scheduler = ASHAScheduler(
    metric="f1",
    mode="max",
    max_t=100,              # Maximum epochs/iterations
    grace_period=10,        # Minimum epochs before stopping
    reduction_factor=3
)
```

**Hyperband**
```python
from ray.tune.schedulers import HyperBandScheduler

scheduler = HyperBandScheduler(
    metric="f1",
    mode="max",
    max_t=100
)
```

### Search Algorithms

**Optuna (Recommended)**
```python
from ray.tune.search.optuna import OptunaSearch

search_alg = OptunaSearch(
    metric="f1",
    mode="max"
)
```

**Hyperopt**
```python
from ray.tune.search.hyperopt import HyperOptSearch

search_alg = HyperOptSearch(
    metric="f1",
    mode="max"
)
```

## Best Practices

### 1. Experiment Organization

- Use descriptive experiment names
- Tag runs with relevant metadata
- Log hyperparameters, metrics, and artifacts
- Use consistent naming conventions

### 2. Model Versioning

- Register models with semantic versioning
- Use stages: Staging, Production, Archived
- Document model versions with descriptions and tags
- Track model lineage (data version, code version)

### 3. Hyperparameter Tuning

- Start with small search spaces
- Use early stopping (ASHA scheduler)
- Limit concurrent trials based on resources
- Use cross-validation for robust results
- Log all trials to MLflow

### 4. Reproducibility

- Set random seeds
- Log environment information (Python version, package versions)
- Save preprocessing artifacts
- Version control code and configurations

## Troubleshooting

### MLflow Server Won't Start

```bash
# Check if port is in use
lsof -i :5000

# Kill process if needed
kill -9 <PID>

# Or use different port
mlflow server --port 5001
```

### Ray Tune Memory Issues

```python
# Reduce concurrent trials
run_hpo(..., max_concurrent_trials=2)

# Reduce number of samples
run_hpo(..., num_samples=10)
```

### MLflow Connection Errors

```python
# Verify server is running
import requests
response = requests.get("http://127.0.0.1:5000")
print(response.status_code)  # Should be 200

# Check firewall/network settings
# Ensure tracking_uri is correct
```

## Quick Start Example

```bash
# 1. Start MLflow server
python scripts/setup_mlflow.py --action start

# 2. Open new terminal and train models
cd notebooks
jupyter notebook 02_model_training.ipynb

# 3. Run all cells in notebook

# 4. View results in MLflow UI
# Open http://127.0.0.1:5000 in browser
```

## Next Steps

After completing model training:

1. **Model Deployment**: Deploy best model as REST API (see `docs/deployment.md`)
2. **Monitoring**: Set up data drift and model performance monitoring (see `monitoring/README.md`)
3. **Orchestration**: Automate training pipeline with Airflow (see `orchestration/README.md`)
4. **CI/CD**: Set up continuous integration and deployment pipelines

## Resources

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Ray Tune Documentation](https://docs.ray.io/en/latest/tune/index.html)
- [Scikit-learn Model Selection](https://scikit-learn.org/stable/model_selection.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
