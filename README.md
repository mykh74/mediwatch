# MediWatch

Predicting patient readmission through Machine Learning + MLOps best practices.

## Links
Trello: https://trello.com/b/KPd4h1lW/mediwatch
Github: https://github.com/mykh74/mediwatch


## Project Overview

MediWatch is an end-to-end MLOps project for predicting hospital patient readmission using the diabetes readmission dataset from Kaggle. The project demonstrates production-ready ML practices including automated data pipelines, experiment tracking, model registry, and deployment preparation.

## Project Status

✅ **Completed**: Data Exploration and Preprocessing  
✅ **Completed**: MLOps Tooling Setup (MLflow + Ray Tune)  
✅ **Completed**: Model Development and Training  
✅ **Completed**: Model Deployment (FastAPI REST API)  
✅ **Completed**: Monitoring (Evidently drift detection)  
✅ **Completed**: Orchestration (Airflow DAGs)

## Key Features

- **Production-Grade Data Pipeline**: Automated preprocessing with artifact management (no data leakage)
- **Multiple ML Models**: 6 baseline algorithms (Logistic Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost)
- **Hyperparameter Optimization**: Ray Tune with ASHA scheduler for efficient HPO
- **Experiment Tracking**: MLflow for comprehensive experiment tracking and comparison
- **Model Registry**: MLflow model registry with staging and production promotion
- **Reproducible Workflows**: Consistent preprocessing, training, and evaluation pipelines

## What's in this repo

### Notebooks
- ✅ `01_eda_and_preprocessing.ipynb` - Comprehensive EDA with 30+ cells
- ✅ `02_model_training.ipynb` - Complete model training workflow

### Source Code (`src/mediwatch/`)
- ✅ `data/` - Data loading and preprocessing with artifact management
- ✅ `features/` - Feature engineering utilities
- ✅ `models/` - Training (6 models), evaluation, and HPO (Ray Tune)
- ✅ `registry/` - MLflow model registry management
- 📋 `inference/` - Inference pipeline (planned)

### Scripts
- ✅ `download_data.py` - Automated Kaggle dataset download
- ✅ `preprocess_data.py` - Data preprocessing pipeline
- ✅ `setup_mlflow.py` - MLflow server setup and initialization

### Infrastructure
- ✅ `api/` - REST inference API with FastAPI (complete implementation)
- ✅ `orchestration/` - Airflow DAGs for pipeline automation
- ✅ `monitoring/` - Evidently drift detection and monitoring

### Documentation
- ✅ `docs/mlops_setup.md` - Comprehensive MLOps setup guide
- ✅ `docs/quick_start.md` - Quick start guide
- ✅ `docs/data_preprocessing.md` - Data preprocessing documentation
- ✅ `docs/model_training.md` - Model training guide
- ✅ `docs/deployment.md` - Complete deployment guide

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Dataset

```bash
# Option A: Using Kaggle API (recommended)
# First, set up Kaggle API credentials: https://github.com/Kaggle/kaggle-api
python scripts/download_data.py --verify

# Option B: Manual download
# Visit: https://www.kaggle.com/datasets/brandao/diabetes
# Save to: data/raw/diabetic_data.csv
```

### 3. Run EDA and Preprocessing

```bash
# Option A: Interactive notebook
jupyter notebook notebooks/01_eda_and_preprocessing.ipynb

# Option B: Automated preprocessing
python scripts/preprocess_data.py
```

### 4. Train Models

```bash
# Start MLflow server
python scripts/setup_mlflow.py --action start

# Open training notebook
jupyter notebook notebooks/02_model_training.ipynb

# View results in MLflow UI: http://127.0.0.1:5000
```

## Documentation

- 🚀 [Quick Start Guide](docs/quick_start.md) - Complete end-to-end guide
- 🔧 [MLOps Setup](docs/mlops_setup.md) - MLflow, Ray Tune, model registry
- 📘 [Data Preprocessing Guide](docs/data_preprocessing.md) - Preprocessing workflow
- 📊 [Model Training Guide](docs/model_training.md) - Training and evaluation
- 📄 [Project Requirements](PROJECT_REQUIREMENTS.md) - Full project specification

## Project Structure

```
MediWatch/
├── data/
│   ├── raw/                    # Raw datasets
│   └── processed/              # Preprocessed train/test + artifacts
├── notebooks/
│   ├── 01_eda_and_preprocessing.ipynb  ✅ Comprehensive EDA
│   └── 02_model_training.ipynb         ✅ Model training workflow
├── src/mediwatch/
│   ├── data/
│   │   ├── load.py             ✅ Kaggle data loading
│   │   └── preprocess.py       ✅ Preprocessing pipeline
│   ├── features/
│   │   └── build_features.py   ✅ Feature engineering
│   ├── models/
│   │   ├── train.py            ✅ 6 baseline models + MLflow
│   │   ├── evaluate.py         ✅ Comprehensive evaluation
│   │   └── tune.py             ✅ Ray Tune HPO
│   ├── inference/
│   │   ├── predict.py          ✅ Inference pipeline with MLflow
│   │   └── schema.py           ✅ Request/response schemas
│   └── registry/
│       └── mlflow_registry.py  ✅ Model registry management
├── scripts/
│   ├── download_data.py        ✅ Dataset download
│   ├── preprocess_data.py      ✅ Preprocessing automation
│   └── setup_mlflow.py         ✅ MLflow server setup
├── api/
│   ├── main.py                 ✅ FastAPI application (complete)
│   └── Dockerfile              ✅ API containerization
├── orchestration/airflow/
│   └── dags/
│       └── mediwatch_pipeline.py  ✅ Complete Airflow DAG
├── monitoring/evidently/
│   └── generate_report.py      ✅ Drift detection & monitoring
└── docs/                       ✅ Comprehensive documentation
```

## Features Implemented

### Data Preprocessing ✅

- **Automated Kaggle download** with API integration
- **Comprehensive EDA notebook** (30+ cells, detailed analysis)
- **Production-grade preprocessing**:
  - Smart missing value imputation
  - Feature engineering (age groups, medical history, interactions)
  - One-hot encoding for categorical features
  - Artifact management (no data leakage)
  - Train/test split with stratification
- **CLI automation scripts** for reproducibility

### Model Training ✅

- **6 Baseline Models**:
  - Logistic Regression
  - Random Forest
  - Gradient Boosting
  - XGBoost
  - LightGBM
  - CatBoost
- **Comprehensive Evaluation**:
  - Accuracy, Precision, Recall, F1 Score
  - ROC-AUC and ROC curves
  - Confusion matrices
  - Cross-validation
- **Hyperparameter Optimization**:
  - Ray Tune integration with ASHA scheduler
  - Model-specific search spaces
  - Optuna search algorithm
  - Parallel trial execution
- **MLflow Integration**:
  - Experiment tracking
  - Metric and parameter logging
  - Model registry
  - Model versioning and staging
- **Training Notebook**: Complete workflow from data loading to model registration

### MLOps Infrastructure ✅

- **MLflow Setup**:
  - Server initialization scripts
  - Experiment management
  - Model registry with staging
  - Production promotion workflow
- **Ray Tune Integration**:
  - Automated hyperparameter search
  - Early stopping with ASHA
  - Multi-model tuning support
- **Documentation**:
  - Comprehensive MLOps setup guide
  - Quick start guide
  - Training and evaluation guides

### Deployment ✅

- **FastAPI REST API**:
  - Health check and model info endpoints
  - Single and batch prediction endpoints
  - Request/response validation with Pydantic
  - MLflow model integration
  - Production-ready with error handling
- **Inference Module**:
  - ModelPredictor class for model management
  - Preprocessing integration
  - Risk level classification (Low/Medium/High)
  - Batch prediction support
- **Docker Support**:
  - Production Dockerfile with health checks
  - Multi-stage builds
  - Environment configuration
- **Deployment Documentation**:
  - Local development setup
  - Docker deployment
  - Kubernetes deployment manifests
  - Production considerations

### Monitoring ✅

- **Evidently Integration**:
  - Data drift detection
  - Target drift monitoring
  - Model performance tracking
  - Automated report generation
  - Quick drift check API
- **Monitoring Reports**:
  - HTML reports with visualizations
  - Drift metrics and thresholds
  - Missing value detection
  - Feature distribution comparison

### Orchestration ✅

- **Airflow DAG**:
  - Complete ML pipeline automation
  - Data download and preprocessing
  - Baseline model training
  - Hyperparameter optimization
  - Model evaluation and selection
  - Model registration and promotion
  - Drift monitoring integration
  - Scheduled weekly execution
- **Pipeline Tasks**:
  - 9 interconnected tasks
  - XCom for metric sharing
  - Conditional model promotion
  - Error handling and retries

## Usage Examples

### Train a Model

```python
from mediwatch.models.train import train_model
import pandas as pd

# Load preprocessed data
train_df = pd.read_csv('data/processed/train.csv')
X_train = train_df.drop(columns=['readmitted'])
y_train = train_df['readmitted']

# Train model with MLflow tracking
model_artifacts = train_model(
    x_train=X_train,
    y_train=y_train,
    model_name="random_forest",
    track_mlflow=True,
    experiment_name="mediwatch-readmission"
)

# Model is automatically logged to MLflow
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

### Hyperparameter Tuning

```python
from mediwatch.models.tune import run_hpo

# Run Ray Tune optimization
hpo_results = run_hpo(
    x_train=X_train,
    y_train=y_train,
    model_name="xgboost",
    num_samples=20,  # 20 trials
    cv=3,
    mlflow_experiment_name="mediwatch-readmission"
)

print(f"Best config: {hpo_results['best_config']}")
print(f"Best F1: {hpo_results['best_score']:.4f}")
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
probabilities = model.predict_proba(X_test)
```

### Apply Preprocessing for Inference

```python
from mediwatch.data.preprocess import apply_preprocessing, PreprocessingArtifacts

# Load saved artifacts
artifacts = PreprocessingArtifacts.load('data/processed/preprocessing_artifacts.pkl')

# Apply to new data (no data leakage!)
X_new = apply_preprocessing(new_data, artifacts)
```

## Next Steps (Planned)

### 1. Model Deployment 📋
- FastAPI REST API for inference
- Docker containerization
- Kubernetes deployment
- Load balancing and scaling

### 2. Model Monitoring 📋
- Evidently for drift detection
- Data quality monitoring
- Model performance tracking
- Alerting system

### 3. Orchestration 📋
- Airflow DAGs for automation
- Scheduled retraining
- Data pipeline orchestration
- CI/CD integration

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

# Type checking
mypy src/
```

## Next Steps

### Immediate (Week 1-2)

- [x] Data exploration and preprocessing
- [ ] Implement baseline models
- [ ] Set up MLflow experiment tracking
- [ ] Hyperparameter tuning with RayTune

### Short-term (Week 3-4)

- [ ] Model packaging and deployment
- [ ] REST API implementation
- [ ] Airflow pipeline orchestration
- [ ] Evidently monitoring setup

### Long-term (Week 5-6)

- [ ] CI/CD pipeline (Jenkins)
- [ ] Kubernetes deployment
- [ ] Drift detection and retraining
- [ ] Complete documentation and video

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## References

- **Dataset**: [Kaggle Diabetes Dataset](https://www.kaggle.com/datasets/brandao/diabetes)
- **Paper**: [Impact of HbA1c Measurement on Hospital Readmission Rates](https://www.hindawi.com/journals/bmri/2014/781670/)
- **MLflow**: https://mlflow.org/
- **Airflow**: https://airflow.apache.org/
- **Evidently**: https://evidentlyai.com/

## License

MIT License - see LICENSE file for details

## Contact

For questions or issues, please open a GitHub issue.
