# MediWatch: Quick Start Guide

Complete guide to get started with the MediWatch patient readmission prediction system.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Kaggle account (for dataset download)
- 8GB+ RAM recommended

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd MediWatch
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Kaggle API

```bash
# Create Kaggle API directory
mkdir -p ~/.kaggle

# Download kaggle.json from Kaggle.com (Account → API → Create New Token)
# Move to ~/.kaggle/
mv ~/Downloads/kaggle.json ~/.kaggle/

# Set permissions
chmod 600 ~/.kaggle/kaggle.json
```

## Project Workflow

### Phase 1: Data Exploration and Preprocessing

#### Step 1: Download Dataset

```bash
python scripts/download_data.py
```

This downloads the diabetes readmission dataset from Kaggle.

#### Step 2: Run EDA Notebook

```bash
jupyter notebook notebooks/01_eda_and_preprocessing.ipynb
```

Run all cells to:
- Explore data distribution
- Analyze missing values
- Engineer features
- Perform feature selection

#### Step 3: Preprocess Data

```bash
python scripts/preprocess_data.py
```

This creates:
- `data/processed/train.csv`: Training set
- `data/processed/test.csv`: Test set
- `data/processed/preprocessing_artifacts.pkl`: Fitted transformers

**Output:**
```
✓ Preprocessed data saved to data/processed/
  Training set: 60,000+ samples
  Test set: 20,000+ samples
  Features: 80+
```

### Phase 2: Model Training and Evaluation

#### Step 1: Start MLflow Server

```bash
# Terminal 1 - Start MLflow server
python scripts/setup_mlflow.py --action start

# Or manually (using virtual environment)
./.venv/bin/mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns

# Or run in background
nohup ./.venv/bin/mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlruns.db --default-artifact-root ./mlruns > mlflow.log 2>&1 &
```

#### Step 2: Run Training Notebook

```bash
# Terminal 2 - Open Jupyter
jupyter notebook notebooks/02_model_training.ipynb
```

Run all cells to:
1. Load preprocessed data
2. Train baseline models (6 algorithms)
3. Evaluate and compare models
4. Run hyperparameter optimization
5. Register best model

**Expected Results:**
- 6 baseline models trained
- F1 scores: 0.65-0.75 (varies by model)
- Best model automatically registered in MLflow

#### Step 3: View Results in MLflow UI

Open browser: http://127.0.0.1:5000

You can:
- Compare all experiments
- View metrics and parameters
- Analyze model performance
- Download model artifacts

### Phase 3: Model Registry and Deployment Prep

#### Register Best Model

```python
from mediwatch.registry.mlflow_registry import get_best_run, register_model

# Find best model
best_run = get_best_run(
    experiment_name="mediwatch-readmission",
    metric="test_f1"
)

# Register
model_uri = f"runs:/{best_run.info.run_id}/model"
register_model(
    model_uri=model_uri,
    model_name="mediwatch_readmission_classifier"
)
```

#### Promote to Production

```python
from mediwatch.registry.mlflow_registry import promote_model_to_production

promote_model_to_production(
    model_name="mediwatch_readmission_classifier"
)
```

## Project Structure

```
MediWatch/
├── data/
│   ├── raw/                    # Raw Kaggle dataset
│   └── processed/              # Preprocessed train/test sets
├── notebooks/
│   ├── 01_eda_and_preprocessing.ipynb   # Data exploration
│   └── 02_model_training.ipynb          # Model training
├── src/mediwatch/
│   ├── data/                   # Data loading and preprocessing
│   ├── features/               # Feature engineering
│   ├── models/                 # Training, evaluation, tuning
│   └── registry/               # MLflow model registry
├── scripts/
│   ├── download_data.py        # Dataset download
│   ├── preprocess_data.py      # Data preprocessing
│   └── setup_mlflow.py         # MLflow setup
├── docs/
│   ├── mlops_setup.md          # Detailed MLOps guide
│   └── quick_start.md          # This file
└── requirements.txt            # Python dependencies
```

## Common Tasks

### Train a Single Model

```python
from mediwatch.models.train import train_model
import pandas as pd

# Load data
train_df = pd.read_csv('data/processed/train.csv')
X_train = train_df.drop(columns=['readmitted'])
y_train = train_df['readmitted']

# Train
model_artifacts = train_model(
    x_train=X_train,
    y_train=y_train,
    model_name="random_forest",
    track_mlflow=True,
    experiment_name="mediwatch-readmission"
)
```

### Evaluate a Model

```python
from mediwatch.models.evaluate import evaluate_model
import pandas as pd

# Load test data
test_df = pd.read_csv('data/processed/test.csv')
X_test = test_df.drop(columns=['readmitted'])
y_test = test_df['readmitted']

# Evaluate
metrics = evaluate_model(
    pipeline=model_artifacts.pipeline,
    x_test=X_test,
    y_test=y_test,
    track_mlflow=True
)

print(f"F1 Score: {metrics['f1']:.4f}")
print(f"ROC AUC: {metrics['roc_auc']:.4f}")
```

### Tune Hyperparameters

```python
from mediwatch.models.tune import run_hpo

# Run optimization
hpo_results = run_hpo(
    x_train=X_train,
    y_train=y_train,
    model_name="xgboost",
    num_samples=20,
    cv=3,
    mlflow_experiment_name="mediwatch-readmission"
)

print(f"Best config: {hpo_results['best_config']}")
print(f"Best F1 score: {hpo_results['best_score']:.4f}")
```

### Load Model from Registry

```python
from mediwatch.registry.mlflow_registry import load_best_model

# Load production model
model = load_best_model(
    model_name="mediwatch_readmission_classifier",
    stage="Production"
)

# Make predictions
predictions = model.predict(X_test)
```

## Available Models

| Model | Description | Training Time | Performance |
|-------|-------------|---------------|-------------|
| Logistic Regression | Linear baseline | Fast | Good |
| Random Forest | Ensemble of trees | Medium | Very Good |
| Gradient Boosting | Boosted trees | Medium | Very Good |
| XGBoost | Optimized gradient boosting | Medium-Fast | Excellent |
| LightGBM | Fast gradient boosting | Fast | Excellent |

## Tips for Best Results

### 1. Data Preprocessing
- Always use the same artifacts for train/test/inference
- No data leakage - transformers fitted only on training data
- Handle missing values appropriately

### 2. Model Selection
- Start with Random Forest as baseline
- Try XGBoost/LightGBM for better performance
- Use cross-validation for robust evaluation

### 3. Hyperparameter Tuning
- Start with default parameters
- Tune top 2-3 models after initial comparison
- Use Ray Tune with ASHA scheduler for efficiency
- Aim for 20-50 trials per model

### 4. MLflow Best Practices
- Always log experiments with descriptive names
- Tag runs with relevant metadata
- Compare multiple runs before selecting best
- Use model registry for deployment

## Troubleshooting

### Dataset Download Fails

```bash
# Ensure Kaggle API is configured
kaggle datasets list

# If fails, check ~/.kaggle/kaggle.json exists and has correct permissions
chmod 600 ~/.kaggle/kaggle.json
```

### MLflow Server Won't Start

```bash
# Check if port 5000 is already in use
lsof -i :5000

# Use different port
mlflow server --port 5001

# Update tracking URI in code
MLFLOW_TRACKING_URI = "http://127.0.0.1:5001"
```

### Memory Errors During Training

```python
# Reduce batch size for Ray Tune
run_hpo(..., max_concurrent_trials=2)

# Use smaller subset for initial testing
X_train_sample = X_train.sample(n=10000, random_state=42)
y_train_sample = y_train.loc[X_train_sample.index]
```

### Import Errors

```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or add in notebooks
import sys
sys.path.insert(0, '../src')
```

## Next Steps

After completing the quick start:

1. **Model Deployment**
   - Deploy as REST API with FastAPI
   - See `api/README.md` (coming soon)

2. **Model Monitoring**
   - Set up Evidently for drift detection
   - See `monitoring/README.md`

3. **Orchestration**
   - Automate pipeline with Airflow
   - See `orchestration/README.md`

4. **Production Deployment**
   - Dockerize application
   - Deploy to cloud (AWS/GCP/Azure)

## Resources

- **Project Documentation**: `docs/`
- **MLOps Guide**: `docs/mlops_setup.md`
- **Data Preprocessing**: `docs/data_preprocessing.md`
- **Model Training**: `docs/model_training.md`

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review documentation in `docs/`
3. Check MLflow logs in `mlruns/`
4. Create an issue in the repository

## Summary

You've now:
- ✅ Set up the environment
- ✅ Downloaded and preprocessed data
- ✅ Trained multiple ML models
- ✅ Evaluated and compared models
- ✅ Optimized hyperparameters
- ✅ Registered best model in MLflow

**Next:** Deploy your model and set up monitoring! 🚀
