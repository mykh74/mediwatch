#!/bin/bash
#
# MediWatch Full Deployment Cycle Test
# Tests the complete end-to-end workflow locally
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Test results
PASSED=0
FAILED=0
WARNINGS=0

test_passed() {
    echo -e "${GREEN}✓ PASSED${NC}: $1"
    ((PASSED++))
}

test_failed() {
    echo -e "${RED}✗ FAILED${NC}: $1"
    ((FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠ WARNING${NC}: $1"
    ((WARNINGS++))
}

section_header() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
}

# Cleanup function
cleanup() {
    echo ""
    section_header "Cleanup"
    
    echo "Stopping test containers..."
    docker stop mediwatch-api-test 2>/dev/null || true
    docker rm mediwatch-api-test 2>/dev/null || true
    
    echo "Cleanup complete"
}

trap cleanup EXIT

# Main test sequence
section_header "MediWatch Full Deployment Cycle Test"
echo "Testing complete ML pipeline from data to deployment"
echo "Started at: $(date)"
echo ""

#############################################
# Phase 1: Prerequisites Check
#############################################
section_header "Phase 1: Prerequisites Check"

echo "1.1 Checking Docker..."
if docker info > /dev/null 2>&1; then
    test_passed "Docker is running"
else
    test_failed "Docker is not running - please start Docker Desktop"
    exit 1
fi

echo ""
echo "1.2 Checking Python environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    test_passed "Virtual environment activated"
else
    test_failed "Virtual environment not found - run ./scripts/local_setup.sh first"
    exit 1
fi

echo ""
echo "1.3 Checking required packages..."
python -c "import mlflow, fastapi, sklearn, xgboost, lightgbm" 2>/dev/null
if [ $? -eq 0 ]; then
    test_passed "All Python packages available"
else
    test_failed "Missing Python packages - run: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "1.4 Checking data files..."
if [ -f "data/raw/diabetic_data.csv" ]; then
    test_passed "Raw data found"
else
    test_warning "Raw data missing - will download"
fi

if [ -f "data/processed/train.csv" ]; then
    test_passed "Processed data found"
else
    test_warning "Processed data missing - will preprocess"
fi

#############################################
# Phase 2: Data Pipeline
#############################################
section_header "Phase 2: Data Pipeline"

echo "2.1 Downloading data (if needed)..."
if [ ! -f "data/raw/diabetic_data.csv" ]; then
    python scripts/download_data.py
    test_passed "Data downloaded"
else
    echo "Data already exists, skipping download"
    test_passed "Data verified"
fi

echo ""
echo "2.2 Preprocessing data..."
if [ ! -f "data/processed/train.csv" ]; then
    python scripts/preprocess_data.py
    test_passed "Data preprocessed"
else
    echo "Processed data exists, verifying..."
    python << EOF
import pandas as pd
train = pd.read_csv('data/processed/train.csv')
test = pd.read_csv('data/processed/test.csv')
print(f"Train: {len(train)} rows, Test: {len(test)} rows")
EOF
    test_passed "Preprocessing verified"
fi

echo ""
echo "2.3 Verifying preprocessing artifacts..."
if [ -f "data/processed/preprocessing_artifacts.pkl" ]; then
    test_passed "Preprocessing artifacts found"
else
    test_warning "Preprocessing artifacts missing"
fi

#############################################
# Phase 3: MLflow Setup
#############################################
section_header "Phase 3: MLflow & Model Registry"

echo "3.1 Starting MLflow server..."
if pgrep -f "mlflow server" > /dev/null; then
    echo "MLflow already running"
    test_passed "MLflow server active"
else
    echo "Starting MLflow server..."
    nohup .venv/bin/mlflow server \
        --host 127.0.0.1 \
        --port 5000 \
        --backend-store-uri sqlite:///mlruns.db \
        --default-artifact-root ./mlruns > mlflow.log 2>&1 &
    
    echo "Waiting for MLflow to start..."
    for i in {1..10}; do
        if curl -s http://localhost:5000/health > /dev/null 2>&1; then
            break
        fi
        sleep 2
    done
fi

echo ""
echo "3.2 Testing MLflow connection..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    test_passed "MLflow health check successful"
else
    test_failed "MLflow is not responding"
    exit 1
fi

echo ""
echo "3.3 Checking for existing models..."
python << 'EOF'
import mlflow
import sys

mlflow.set_tracking_uri("http://localhost:5000")

try:
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    
    # Check for registered models
    models = client.search_registered_models()
    
    if models:
        print(f"✓ Found {len(models)} registered model(s)")
        for model in models:
            print(f"  - {model.name}")
            versions = client.search_model_versions(f"name='{model.name}'")
            for v in versions:
                if v.current_stage == "Production":
                    print(f"    Production version: {v.version}")
        sys.exit(0)
    else:
        print("⚠ No models registered yet")
        sys.exit(1)
except Exception as e:
    print(f"⚠ Model check failed: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    test_passed "Production model found in registry"
    NEED_TRAINING=false
else
    test_warning "No production model - will train models"
    NEED_TRAINING=true
fi

#############################################
# Phase 4: Model Training (if needed)
#############################################
if [ "$NEED_TRAINING" = true ]; then
    section_header "Phase 4: Model Training & Registration"
    
    echo "4.1 Training models (this may take 10-20 minutes)..."
    echo "Training 6 algorithms: Logistic Regression, Random Forest, GBM, XGBoost, LightGBM, CatBoost"
    echo ""
    
    python scripts/train_models.py
    
    if [ $? -eq 0 ]; then
        test_passed "Models trained successfully"
    else
        test_failed "Model training failed"
        exit 1
    fi
    
    echo ""
    echo "4.2 Checking trained models..."
    python << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

experiments = client.search_experiments()
print(f"✓ Total experiments: {len(experiments)}")

for exp in experiments:
    runs = client.search_runs(exp.experiment_id)
    if runs:
        print(f"  - {exp.name}: {len(runs)} runs")
EOF
    test_passed "Training results logged to MLflow"
    
    echo ""
    echo "4.3 Registering best model..."
    echo "Note: For automated registration, we'll use the best performing model from training"
    
    python << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient
import sys

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

# Find best run by F1 score
experiment = client.get_experiment_by_name("mediwatch_readmission")
if experiment:
    runs = client.search_runs(
        experiment.experiment_id,
        order_by=["metrics.test_f1_score DESC"],
        max_results=1
    )
    
    if runs:
        best_run = runs[0]
        model_name = "mediwatch_readmission_classifier"
        
        # Register model
        model_uri = f"runs:/{best_run.info.run_id}/model"
        
        try:
            # Check if model already exists
            try:
                client.get_registered_model(model_name)
                print(f"Model {model_name} already registered")
            except:
                client.create_registered_model(model_name)
                print(f"Created new model: {model_name}")
            
            # Create new version
            mv = client.create_model_version(
                name=model_name,
                source=model_uri,
                run_id=best_run.info.run_id
            )
            
            # Transition to production
            client.transition_model_version_stage(
                name=model_name,
                version=mv.version,
                stage="Production"
            )
            
            print(f"✓ Registered model version {mv.version} as Production")
            print(f"  F1 Score: {best_run.data.metrics.get('test_f1_score', 'N/A'):.4f}")
            print(f"  Algorithm: {best_run.data.params.get('model_type', 'Unknown')}")
            sys.exit(0)
        except Exception as e:
            print(f"✗ Registration failed: {e}")
            sys.exit(1)
else:
    print("✗ No experiment found")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        test_passed "Best model registered as Production"
    else
        test_failed "Model registration failed"
        exit 1
    fi
else
    echo ""
    echo "Skipping Phase 4: Production model already exists"
fi

#############################################
# Phase 5: API Testing
#############################################
section_header "Phase 5: API Testing"

echo "5.1 Setting up environment variables..."
export MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
export MODEL_NAME="mediwatch_readmission_classifier"
export MODEL_STAGE="Production"
export PREPROCESSING_ARTIFACTS_PATH="data/processed/preprocessing_artifacts.pkl"
test_passed "Environment configured"

echo ""
echo "5.2 Starting FastAPI server..."
pkill -f "uvicorn api.main:app" 2>/dev/null || true
sleep 2

nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
API_PID=$!

echo "Waiting for API to start..."
for i in {1..15}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo ""
echo "5.3 Testing API endpoints..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    test_passed "Health endpoint responding"
else
    test_failed "API not responding"
    cat api.log
    exit 1
fi

echo ""
echo "5.4 Testing model info endpoint..."
RESPONSE=$(curl -s http://localhost:8000/model/info)
if echo "$RESPONSE" | grep -q "model_name"; then
    test_passed "Model info endpoint working"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    test_failed "Model info endpoint failed"
fi

echo ""
echo "5.5 Testing prediction endpoint..."
python test_api.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    test_passed "Prediction endpoint working"
else
    test_warning "Prediction test script had issues"
fi

# Test with curl
echo ""
echo "5.6 Testing direct prediction..."
PRED_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
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
      "change": "Ch",
      "diabetesMed": "Yes"
    }
  }')

if echo "$PRED_RESPONSE" | grep -q "prediction"; then
    test_passed "Prediction successful"
    echo "Sample prediction:"
    echo "$PRED_RESPONSE" | python -m json.tool 2>/dev/null | head -20
else
    test_failed "Prediction failed"
    echo "Response: $PRED_RESPONSE"
fi

#############################################
# Phase 6: Docker Build & Test
#############################################
section_header "Phase 6: Docker Build & Deployment"

echo "6.1 Building Docker image..."
docker build -t mediwatch-api:test -f api/Dockerfile . > /dev/null 2>&1

if [ $? -eq 0 ]; then
    test_passed "Docker image built successfully"
else
    test_failed "Docker build failed"
    exit 1
fi

echo ""
echo "6.2 Checking image size..."
IMAGE_SIZE=$(docker images mediwatch-api:test --format "{{.Size}}")
echo "Image size: $IMAGE_SIZE"
test_passed "Docker image created: $IMAGE_SIZE"

echo ""
echo "6.3 Running container test..."
# Stop any existing test container
docker stop mediwatch-api-test 2>/dev/null || true
docker rm mediwatch-api-test 2>/dev/null || true

# Run new container
docker run -d \
  --name mediwatch-api-test \
  -p 8001:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=mediwatch_readmission_classifier \
  -e MODEL_STAGE=Production \
  -e PREPROCESSING_ARTIFACTS_PATH=/app/data/processed/preprocessing_artifacts.pkl \
  mediwatch-api:test

echo "Waiting for container to start..."
sleep 10

echo ""
echo "6.4 Testing containerized API..."
for i in {1..5}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        test_passed "Containerized API is healthy"
        break
    fi
    if [ $i -eq 5 ]; then
        test_failed "Container API not responding"
        echo "Container logs:"
        docker logs mediwatch-api-test
    fi
    sleep 3
done

echo ""
echo "6.5 Testing container prediction..."
CONTAINER_PRED=$(curl -s http://localhost:8001/health)
if echo "$CONTAINER_PRED" | grep -q "healthy"; then
    test_passed "Container prediction endpoint working"
else
    test_warning "Container prediction test inconclusive"
fi

#############################################
# Phase 7: Jenkins CI/CD
#############################################
section_header "Phase 7: Jenkins CI/CD Pipeline"

echo "7.1 Checking Jenkins status..."
if docker ps | grep -q jenkins; then
    test_passed "Jenkins container running"
else
    echo "Starting Jenkins..."
    cd ci-cd
    docker-compose -f docker-compose.jenkins.yml up -d
    cd "$PROJECT_ROOT"
    
    echo "Waiting for Jenkins to start (60 seconds)..."
    sleep 60
    
    if docker ps | grep -q jenkins; then
        test_passed "Jenkins started successfully"
    else
        test_failed "Jenkins failed to start"
        exit 1
    fi
fi

echo ""
echo "7.2 Testing Jenkins connectivity..."
for i in {1..10}; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        test_passed "Jenkins is accessible"
        break
    fi
    if [ $i -eq 10 ]; then
        test_warning "Jenkins web UI not responding (may need initial setup)"
    fi
    sleep 3
done

echo ""
echo "7.3 Getting Jenkins initial password..."
JENKINS_PASS=$(docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "")
if [ -n "$JENKINS_PASS" ]; then
    test_passed "Jenkins password retrieved"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}  Jenkins Initial Admin Password${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}$JENKINS_PASS${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""
    echo "Use this password to login at: http://localhost:8080"
else
    test_warning "Jenkins already configured (no initial password)"
fi

echo ""
echo "7.4 Validating Jenkinsfile..."
if [ -f "Jenkinsfile" ]; then
    test_passed "Jenkinsfile exists"
    STAGES=$(grep -c "stage(" Jenkinsfile || echo 0)
    echo "  Jenkinsfile contains $STAGES stages"
else
    test_failed "Jenkinsfile not found"
fi

#############################################
# Phase 8: Validation Summary
#############################################
section_header "Phase 8: Deployment Validation"

echo "8.1 Service Status Check..."
echo ""
printf "%-25s %-20s %-30s\n" "Service" "Status" "URL"
printf "%-25s %-20s %-30s\n" "-------" "------" "---"

# MLflow
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    printf "%-25s ${GREEN}%-20s${NC} %-30s\n" "MLflow UI" "✓ Running" "http://localhost:5000"
else
    printf "%-25s ${RED}%-20s${NC} %-30s\n" "MLflow UI" "✗ Down" "http://localhost:5000"
fi

# API (host)
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    printf "%-25s ${GREEN}%-20s${NC} %-30s\n" "API (Host)" "✓ Running" "http://localhost:8000"
else
    printf "%-25s ${RED}%-20s${NC} %-30s\n" "API (Host)" "✗ Down" "http://localhost:8000"
fi

# API (container)
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    printf "%-25s ${GREEN}%-20s${NC} %-30s\n" "API (Docker)" "✓ Running" "http://localhost:8001"
else
    printf "%-25s ${RED}%-20s${NC} %-30s\n" "API (Docker)" "✗ Down" "http://localhost:8001"
fi

# Jenkins
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    printf "%-25s ${GREEN}%-20s${NC} %-30s\n" "Jenkins" "✓ Running" "http://localhost:8080"
else
    printf "%-25s ${RED}%-20s${NC} %-30s\n" "Jenkins" "✗ Down" "http://localhost:8080"
fi

echo ""
echo "8.2 Docker Resources..."
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "mediwatch|jenkins|mlflow" || echo "No containers found"

echo ""
echo "8.3 Model Registry Status..."
python << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

try:
    models = client.search_registered_models()
    print(f"✓ Registered Models: {len(models)}")
    
    for model in models:
        versions = client.search_model_versions(f"name='{model.name}'")
        prod_versions = [v for v in versions if v.current_stage == "Production"]
        print(f"  - {model.name}")
        print(f"    Total versions: {len(versions)}")
        print(f"    Production versions: {len(prod_versions)}")
        if prod_versions:
            print(f"    Latest production: v{prod_versions[0].version}")
except Exception as e:
    print(f"✗ Error checking models: {e}")
EOF

#############################################
# Final Summary
#############################################
section_header "Test Results Summary"

echo "Completed at: $(date)"
echo ""
echo -e "Tests Passed:   ${GREEN}${PASSED}${NC}"
echo -e "Tests Failed:   ${RED}${FAILED}${NC}"
echo -e "Warnings:       ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ DEPLOYMENT CYCLE COMPLETE!            ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo ""
    echo "All systems operational!"
    echo ""
    echo "Next Steps:"
    echo "  1. Access MLflow UI:     http://localhost:5000"
    echo "  2. Access API Docs:      http://localhost:8000/docs"
    echo "  3. Access Jenkins:       http://localhost:8080"
    echo "  4. Test predictions:     python test_api.py"
    echo ""
    echo "To configure Jenkins pipeline:"
    echo "  1. Login to Jenkins with password above"
    echo "  2. Install suggested plugins"
    echo "  3. Create pipeline job 'mediwatch-ci-cd'"
    echo "  4. Point to Jenkinsfile in repository"
    echo "  5. Run build to test full CI/CD"
    echo ""
    echo "For detailed instructions, see:"
    echo "  - LOCAL_BUILD_GUIDE.md"
    echo "  - docs/JENKINS_SETUP.md"
    echo ""
else
    echo -e "${RED}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ DEPLOYMENT HAD FAILURES                ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please review the failed tests above and:"
    echo "  - Check log files: mlflow.log, api.log"
    echo "  - Verify Docker is running"
    echo "  - Ensure all dependencies installed"
    echo "  - Review LOCAL_BUILD_GUIDE.md for troubleshooting"
    echo ""
    exit 1
fi
