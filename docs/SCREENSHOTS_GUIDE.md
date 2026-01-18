# MediWatch - Screenshots and Demo Guide

This guide helps you capture screenshots and demonstrate the complete MediWatch system for project submission.

---

## Required Screenshots

### 1. Data Pipeline

**1.1 EDA Notebook**
- Open: `notebooks/01_eda_and_preprocessing.ipynb`
- Capture: First few cells showing data loading and basic stats
- Capture: Visualization outputs (distributions, correlations)
- Capture: Final cell showing successful preprocessing

**1.2 Preprocessing Artifacts**
```bash
ls -la data/processed/
```
- Capture terminal showing generated files

### 2. Model Training

**2.1 Training Notebook**
- Open: `notebooks/02_model_training.ipynb`
- Capture: Model training cells with output
- Capture: Evaluation metrics table
- Capture: Model comparison results

**2.2 MLflow UI**
```bash
# Start MLflow if not running
mlflow server --host 127.0.0.1 --port 5000
```
- Navigate to: http://localhost:5000
- Capture: Experiments list
- Capture: Run comparison view
- Capture: Model registry page
- Capture: Specific run details with metrics

**2.3 Ray Tune HPO**
- Run HPO from notebook or script
- Capture: Console output showing parallel trials
- Capture: MLflow showing HPO runs

### 3. Inference API

**3.1 Start API**
```bash
cd /Users/michaelkuzmyn/projects/ik/MediWatch
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
- Capture: Terminal showing successful startup

**3.2 Swagger Documentation**
- Navigate to: http://localhost:8000/docs
- Capture: Full API documentation page
- Capture: Expanded endpoint showing request/response schemas

**3.3 Test Prediction**
- Use Swagger UI "Try it out" feature
- Or use curl:
```bash
curl http://localhost:8000/health
```
- Capture: Request and response

### 4. Docker

**4.1 Build Image**
```bash
docker build -t mediwatch-api:latest -f api/Dockerfile .
```
- Capture: Build output (successful completion)

**4.2 List Images**
```bash
docker images | grep mediwatch
```
- Capture: Terminal output

**4.3 Run Container**
```bash
docker run -p 8000:8000 mediwatch-api:latest
```
- Capture: Container logs showing startup

**4.4 Verify Container**
```bash
docker ps | grep mediwatch
curl http://localhost:8000/health
```
- Capture: Running container and health check

### 5. CI/CD (Jenkins)

**5.1 Jenkins Dashboard**
```bash
cd ci-cd
./scripts/start_jenkins.sh
```
- Navigate to: http://localhost:8080
- Capture: Jenkins dashboard
- Capture: mediwatch-ci-cd job page

**5.2 Pipeline Configuration**
- Open job configuration
- Capture: Pipeline section showing Jenkinsfile
- Capture: Build triggers section
- Capture: Parameters section

**5.3 Build Execution**
- Trigger build manually
- Capture: Build in progress
- Capture: Console output (partial)
- Capture: Successful build result
- Capture: Build history

**5.4 Remote Trigger**
```bash
python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token \
  --deploy-mode docker \
  --monitor
```
- Capture: Terminal showing trigger and monitoring

### 6. Orchestration (Airflow)

**6.1 Airflow UI**
```bash
airflow webserver -p 8080
```
- Navigate to: http://localhost:8080
- Capture: DAGs list
- Capture: mediwatch_ml_pipeline DAG
- Capture: Graph view of DAG
- Capture: Tree view showing task dependencies

**6.2 DAG Execution**
- Trigger DAG manually
- Capture: Running DAG with task statuses
- Capture: Successful completion
- Capture: Task logs (sample)

**6.3 Jenkins Integration DAG**
- Show: `mediwatch_pipeline_with_cicd` DAG
- Capture: Graph view showing Jenkins tasks

### 7. Monitoring (Evidently)

**7.1 Generate Report**
```bash
python monitoring/evidently/generate_report.py
```
- Capture: Terminal output

**7.2 View Report**
- Open generated HTML report in browser
- Capture: Drift detection summary
- Capture: Feature drift visualizations
- Capture: Statistical test results

### 8. Project Structure

**8.1 Directory Tree**
```bash
tree -L 2 -I '__pycache__|*.pyc|.git'
```
- Capture: Project structure

**8.2 Key Files**
```bash
ls -la *.md
ls -la api/
ls -la ci-cd/
ls -la docs/
```
- Capture: File listings

---

## Demo Scenario (End-to-End)

This demonstrates the complete workflow:

### Step 1: Data Preparation
```bash
# Download data
python scripts/download_data.py

# Preprocess
python scripts/preprocess_data.py
```
📸 Capture: Successful execution

### Step 2: Model Training
```bash
# Start MLflow
mlflow server --host 127.0.0.1 --port 5000 &

# Run training notebook or script
jupyter notebook notebooks/02_model_training.ipynb
```
📸 Capture: 
- Training output
- MLflow UI with experiments

### Step 3: Deployment via Jenkins
```bash
# Start Jenkins
cd ci-cd && ./scripts/start_jenkins.sh

# Trigger build
python scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token \
  --deploy-mode docker \
  --run-tests \
  --monitor
```
📸 Capture:
- Jenkins build progress
- Successful deployment
- API health check

### Step 4: Test API
```bash
# Test health endpoint
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Make prediction
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "race": "Caucasian",
      "gender": "Female",
      "age": "[50-60)",
      "time_in_hospital": 3,
      "num_lab_procedures": 41,
      "num_medications": 10,
      "number_diagnoses": 9,
      "diabetesMed": "Yes"
    }
  }'
```
📸 Capture:
- Successful prediction response
- Swagger UI

### Step 5: Monitoring
```bash
# Generate drift report
python monitoring/evidently/generate_report.py
```
📸 Capture: Generated report

### Step 6: Orchestration
```bash
# Start Airflow
airflow scheduler &
airflow webserver -p 8081 &

# Trigger pipeline
airflow dags trigger mediwatch_ml_pipeline
```
📸 Capture: Complete pipeline execution

---

## Video Recording Outline

### 1. Introduction (1 min)
- Project overview
- Technology stack
- Architecture diagram

### 2. Code Tour (2 min)
- Walk through project structure
- Highlight key modules
- Show documentation

### 3. Data Pipeline Demo (2 min)
- Run EDA notebook (fast-forward)
- Show preprocessing output
- Display artifacts

### 4. Model Training Demo (3 min)
- Start MLflow server
- Run training (show one model)
- Navigate MLflow UI
- Show experiment comparison
- Demonstrate model registry

### 5. Deployment Demo (3 min)
- Start Jenkins
- Configure and trigger build
- Monitor build progress
- Show deployed API
- Test prediction endpoint

### 6. Orchestration Demo (2 min)
- Show Airflow DAG
- Trigger pipeline
- Monitor execution
- Show task dependencies

### 7. Monitoring Demo (1 min)
- Generate Evidently report
- Show drift detection results

### 8. Conclusion (1 min)
- Summary of features
- MLOps best practices implemented
- Future enhancements

**Total**: ~15 minutes

---

## Tools for Screenshots

### macOS
```bash
# Full screen: Cmd+Shift+3
# Selection: Cmd+Shift+4
# Window: Cmd+Shift+4, then Space
```

### Terminal Recording
```bash
# Install asciinema
brew install asciinema

# Record session
asciinema rec demo.cast

# Play back
asciinema play demo.cast
```

### Screen Recording
- **macOS**: Cmd+Shift+5 (built-in)
- **OBS Studio**: https://obsproject.com/ (cross-platform)
- **Loom**: https://loom.com/ (easy to use)

---

## Screenshot Checklist

Essential screenshots for submission:

- [ ] EDA notebook outputs
- [ ] Preprocessing artifacts listing
- [ ] Model training results
- [ ] MLflow experiments view
- [ ] MLflow model registry
- [ ] Ray Tune HPO execution
- [ ] FastAPI Swagger docs
- [ ] Successful API prediction
- [ ] Docker image build
- [ ] Docker container running
- [ ] Jenkins dashboard
- [ ] Jenkins pipeline configuration
- [ ] Jenkins build execution
- [ ] Jenkins build success
- [ ] Remote Jenkins trigger
- [ ] Airflow DAGs list
- [ ] Airflow DAG graph view
- [ ] Airflow pipeline execution
- [ ] Evidently drift report
- [ ] Project directory structure

---

## Tips for Good Screenshots

1. **Clean terminal**: Clear history before capturing
2. **Readable fonts**: Use larger font sizes
3. **Highlight key parts**: Use annotations if needed
4. **Context**: Include timestamps, URLs where relevant
5. **Quality**: Use PNG format, not JPG
6. **Organize**: Name files descriptively (e.g., `01_mlflow_experiments.png`)

---

## Creating a Demo Package

```bash
# Create demo directory
mkdir mediwatch-demo
cd mediwatch-demo

# Copy screenshots
mkdir screenshots
# Add your screenshots here

# Create README
cat > README.md << 'EOF'
# MediWatch Demo Package

## Contents
- screenshots/ - System screenshots
- video/ - Demo video (if available)
- logs/ - Sample execution logs
- reports/ - Evidently reports

## Quick Links
- Documentation: ../docs/
- Source Code: ../src/
- Notebooks: ../notebooks/
EOF

# Package for submission
cd ..
tar -czf mediwatch-demo.tar.gz mediwatch-demo/
```

---

## Documentation References

For detailed setup and usage:
- [Quick Start Guide](quick_start.md)
- [Jenkins Setup](JENKINS_SETUP.md)
- [Deployment Guide](deployment.md)
- [MLOps Setup](mlops_setup.md)

---

**Ready to capture your complete MLOps system!** 📸
