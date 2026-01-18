#!/bin/bash
#
# MediWatch Local Setup Script
# Automated setup for local development and testing
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  MediWatch Local Setup${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Step 1: Check Docker
echo -e "${YELLOW}Step 1: Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo ""
    echo "Please start Docker Desktop:"
    echo "  1. Open Docker Desktop from Applications"
    echo "  2. Wait for the whale icon in menu bar"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Step 2: Python virtual environment
echo -e "${YELLOW}Step 2: Setting up Python environment...${NC}"
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv .venv
fi

source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 3: Install dependencies
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"
echo "This may take 3-5 minutes..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install -e . -q
pip install pytest requests -q
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Check data
echo -e "${YELLOW}Step 4: Checking data files...${NC}"
if [ ! -f "data/raw/diabetic_data.csv" ]; then
    echo "Downloading data..."
    python scripts/download_data.py
fi

if [ ! -f "data/processed/train.csv" ]; then
    echo "Preprocessing data..."
    python scripts/preprocess_data.py
fi
echo -e "${GREEN}✓ Data files ready${NC}"
echo ""

# Step 5: Create .env file
echo -e "${YELLOW}Step 5: Creating environment configuration...${NC}"
cat > .env << 'EOF'
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
MODEL_NAME=mediwatch_readmission_classifier
MODEL_STAGE=Production
PREPROCESSING_ARTIFACTS_PATH=data/processed/preprocessing_artifacts.pkl
EOF
echo -e "${GREEN}✓ Environment file created${NC}"
echo ""

# Step 6: Start MLflow
echo -e "${YELLOW}Step 6: Starting MLflow server...${NC}"
if pgrep -f "mlflow server" > /dev/null; then
    echo "MLflow is already running"
else
    nohup .venv/bin/mlflow server \
        --host 127.0.0.1 \
        --port 5000 \
        --backend-store-uri sqlite:///mlruns.db \
        --default-artifact-root ./mlruns > mlflow.log 2>&1 &
    
    echo "Waiting for MLflow to start..."
    sleep 5
    
    if curl -s http://localhost:5000/health > /dev/null; then
        echo -e "${GREEN}✓ MLflow server started${NC}"
    else
        echo -e "${RED}✗ MLflow failed to start${NC}"
        echo "Check mlflow.log for details"
        exit 1
    fi
fi
echo ""

# Step 7: Check models
echo -e "${YELLOW}Step 7: Checking MLflow models...${NC}"
if [ -z "$(ls -A mlruns/1/models/ 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠ No models found. You may need to train models.${NC}"
    echo ""
    echo "To train models, run:"
    echo "  python scripts/train_models.py"
    echo ""
else
    echo -e "${GREEN}✓ Models found in MLflow${NC}"
fi
echo ""

# Step 8: Build Docker image
echo -e "${YELLOW}Step 8: Building Docker image...${NC}"
echo "This may take 5-10 minutes on first run..."
docker build -t mediwatch-api:latest -f api/Dockerfile . -q
echo -e "${GREEN}✓ Docker image built${NC}"
echo ""

# Step 9: Setup Jenkins
echo -e "${YELLOW}Step 9: Setting up Jenkins...${NC}"
if docker ps | grep -q jenkins; then
    echo "Jenkins is already running"
else
    cd ci-cd
    if [ -f "docker-compose.jenkins.yml" ]; then
        docker-compose -f docker-compose.jenkins.yml up -d
        echo "Waiting for Jenkins to start (this takes ~60 seconds)..."
        sleep 30
        echo -e "${GREEN}✓ Jenkins container started${NC}"
    else
        echo -e "${YELLOW}⚠ Jenkins config not found, skipping${NC}"
    fi
    cd "$PROJECT_ROOT"
fi
echo ""

# Summary
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Services running:"
echo -e "  ${GREEN}✓${NC} MLflow UI:     http://localhost:5000"
echo -e "  ${GREEN}✓${NC} Jenkins UI:    http://localhost:8080"
echo ""
echo "To start the API:"
echo -e "  ${YELLOW}cd api${NC}"
echo -e "  ${YELLOW}uvicorn main:app --reload --port 8000${NC}"
echo ""
echo "To test the API:"
echo -e "  ${YELLOW}python test_api.py${NC}"
echo ""
echo "To run Jenkins pipeline:"
echo -e "  ${YELLOW}python ci-cd/scripts/trigger_jenkins.py --job mediwatch-ci-cd${NC}"
echo ""
echo "Get Jenkins initial password:"
echo -e "  ${YELLOW}docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword${NC}"
echo ""
echo "For full documentation, see:"
echo "  - LOCAL_BUILD_GUIDE.md"
echo "  - docs/JENKINS_SETUP.md"
echo "  - docs/deployment.md"
echo ""
echo -e "${GREEN}Ready for local development and testing!${NC}"
echo ""
