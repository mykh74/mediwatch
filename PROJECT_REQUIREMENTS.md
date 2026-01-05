# MediWatch — Project Requirements

## 1. Overview

### 1.1 Problem Statement
MediWatch is a machine learning (ML) and MLOps project that predicts the likelihood of hospital readmission shortly after discharge. The system supports proactive identification of high-risk patients to enable targeted interventions and improved care transitions.

### 1.2 Goals
- Build a predictive model for patient readmission risk using the Kaggle diabetes dataset.
- Implement an end-to-end MLOps lifecycle: data management, training at scale, experiment tracking, packaging, deployment, monitoring, and continuous training.
- Provide reproducible pipelines and documentation to run the system locally and/or via containers.

### 1.3 Out of Scope
- Clinical decision-making automation or treatment recommendation generation.
- Guaranteeing clinical outcomes or regulatory certification.
- Building a full clinical UI/EHR integration (unless explicitly added later).

## 2. Users and Stakeholders

### 2.1 Primary Users
- ML Engineer / Data Scientist: develops features and models; runs experiments.
- MLOps Engineer: deploys and automates pipelines; sets up monitoring and CI/CD.

### 2.2 Secondary Stakeholders
- Healthcare Provider / Analyst (consumer of predictions via API).
- Evaluator/Instructor (assesses tooling, reproducibility, and documentation).

## 3. Data Requirements

### 3.1 Dataset
- Source: Kaggle dataset https://www.kaggle.com/datasets/brandao/diabetes
- The system must support:
  - Train/test split.
  - Optional drift simulation via controlled sampling/splitting or time-like partitioning.

### 3.2 Data Handling
- Must include preprocessing for missing values and data types.
- Must include feature engineering (e.g., encoding, transformations) suitable for the dataset.
- Must persist and reuse transformation artifacts (e.g., encoders/vectorizers) so inference does not fit transformers on production/inference data.

### 3.3 Data Versioning (Recommended)
- Track dataset version / split metadata in a reproducible manner (e.g., file hashes, run parameters, or a data versioning tool).

## 4. Functional Requirements

### 4.1 Exploratory Analysis and Feature Engineering
- Provide an experimentation notebook containing:
  - Exploratory Data Analysis (EDA) with insights.
  - Data cleaning and preprocessing.
  - Feature engineering steps.
  - Baseline and improved model exploration.

### 4.2 Model Training
- Train at least one ML model capable of predicting readmission risk.
- The training process must:
  - Split data into training and testing sets.
  - Produce evaluation metrics appropriate to classification.
  - Save the best-performing model artifact.

### 4.3 Large-Scale Experimentation and Hyperparameter Optimization
- Orchestrate hyperparameter optimization (HPO) using RayTune or an equivalent tool.
- Execute parallel experiments at scale.

### 4.4 Experiment Tracking
- Track all experiments in MLflow (or equivalent), including at minimum:
  - Parameters (hyperparameters and key pipeline settings)
  - Metrics
  - Model artifacts
  - Preprocessing/feature transformation artifacts

### 4.5 Model Selection
- Automatically identify and retrieve the best-performing run/model from the experiment tracker.

### 4.6 Inference API
- Deploy the selected model as a RESTful API endpoint.
- The API must:
  - Accept an input payload representing a patient record compatible with the trained feature schema.
  - Return a prediction response including:
    - Predicted class/label (readmission / no readmission) and/or probability score.
  - Use the exact same preprocessing artifacts as training.

### 4.7 API Documentation
- Provide API documentation via Swagger/OpenAPI or an equivalent mechanism.

### 4.8 Packaging and Deployment
- Package the inference service and model artifacts into a deployable unit.
- Must support containerization using Docker.
- Kubernetes deployment is required only “if required” by the chosen delivery plan; if implemented, provide manifests/helm charts and instructions.

### 4.9 Orchestration
- Orchestrate the end-to-end pipeline (data prep → training → HPO → evaluation → model registration/selection → packaging → deployment) using Airflow or an equivalent orchestrator.
- The orchestration layer must support scheduled or trigger-based execution.

### 4.10 CI/CD Automation
- Automate packaging and deployment using a CI/CD tool such as Jenkins (or equivalent).
- Must support remote triggering of build/deploy jobs.

### 4.11 Monitoring and Drift Detection
- Implement monitoring using Evidently (or equivalent) to detect:
  - Data drift across multiple columns
  - Model drift/performance degradation (where labels are available)
- Must use multiple drift detection measures (examples mentioned: PSI, KS test).
- Monitoring must produce a dashboard or report artifacts.

### 4.12 Continuous Training
- Implement retraining and redeployment logic triggered by drift detection.
- Pipeline must:
  - Detect drift
  - Retrain model (full or incremental approach)
  - Re-evaluate
  - Promote and redeploy if performance gates are met

## 5. Non-Functional Requirements

### 5.1 Reproducibility
- Provide deterministic/reproducible runs where feasible:
  - Seeded splits and training
  - Versioned dependencies
  - Captured configs per run

### 5.2 Reliability
- API must validate inputs and return clear error messages for malformed payloads.
- Pipeline steps must fail fast with actionable logs.

### 5.3 Scalability
- HPO must support parallel execution.
- Deployment should support horizontal scaling if containerized and/or on Kubernetes.

### 5.4 Security and Privacy (Project-appropriate)
- Avoid logging sensitive payload values in plaintext beyond what is required for debugging.
- If secrets are required (MLflow/Jenkins/etc.), store them via environment variables or a secrets manager (not committed to source control).

### 5.5 Observability
- Provide logs for:
  - Training runs
  - API requests (minimal, non-sensitive)
  - Monitoring jobs and drift checks

## 6. System Components (Logical)

### 6.1 Training Pipeline
- Data loading and preprocessing
- Feature engineering
- Model training
- HPO (RayTune or equivalent)
- Experiment logging (MLflow)
- Model selection and registration

### 6.2 Inference Service
- REST API server (framework choice allowed)
- Model artifact loading
- Preprocessing artifact loading
- Prediction endpoint(s)
- OpenAPI/Swagger docs

### 6.3 Orchestration
- DAG/workflow definitions for:
  - Training + HPO
  - Packaging
  - Deployment
  - Drift monitoring
  - Retraining triggers

### 6.4 Monitoring
- Evidently reports/dashboard generation
- Drift metrics computation on new data batches

### 6.5 CI/CD
- Build job:
  - Build Docker image(s)
  - Run checks/tests (if present)
  - Push artifacts to registry (optional)
- Deploy job:
  - Deploy to target runtime (Docker host or Kubernetes)

## 7. Deliverables

### 7.1 Experimentation Notebook
- Jupyter Notebook including EDA, preprocessing, feature engineering, and model exploration.

### 7.2 MLOps Implementation
- Code and configuration that demonstrates:
  - Data management
  - Large-scale training/HPO
  - Experiment tracking
  - Model packaging
  - Deployment + inference
  - Monitoring + drift detection
  - Continuous training/retraining
  - Orchestration (Airflow or equivalent)

### 7.3 Documentation
Documentation must include:
- Setup instructions (tools, dependencies, how to run).
- System architecture (diagram or clear description).
- How to run the full pipeline end-to-end.
- How to run individual components (training, API, monitoring, orchestration).
- Snapshots of executed pipelines (screenshots) and optional video.
- “Future enhancements” section describing possible improvements.

## 8. Acceptance Criteria (Testable)

### 8.1 Notebook
- A notebook exists and runs end-to-end producing:
  - EDA outputs
  - A trained model
  - Evaluation metrics

### 8.2 Experiment Tracking
- MLflow shows multiple runs with logged params, metrics, and artifacts.
- Best run/model can be programmatically selected.

### 8.3 HPO
- RayTune (or equivalent) launches parallel trials and logs results.

### 8.4 Inference API
- API starts successfully and exposes OpenAPI/Swagger docs.
- A sample request returns a valid prediction response.
- Inference uses persisted preprocessing artifacts (no fitting on inference data).

### 8.5 Packaging
- Docker image builds successfully for the inference service.

### 8.6 Monitoring
- Evidently (or equivalent) generates drift reports for multiple columns.
- At least two drift measures are demonstrated (e.g., PSI and KS).

### 8.7 Orchestration and Retraining
- Orchestrator can:
  - Run training pipeline
  - Run monitoring checks
  - Trigger retraining and redeployment when drift criteria are met

### 8.8 CI/CD
- CI/CD job(s) can be triggered to build and deploy the inference artifact.

## 9. Suggested Milestones (Implementation Plan)
- Data exploration and preprocessing
- Feature engineering and baseline model
- MLflow experiment tracking
- RayTune HPO and best-model selection
- Inference API + OpenAPI docs
- Container packaging (Docker)
- Orchestration pipeline (Airflow or equivalent)
- Monitoring (Evidently) + drift detection
- Continuous training trigger + redeploy
- Documentation and user manual
