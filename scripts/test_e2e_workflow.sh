#!/bin/bash

# End-to-End CI/CD Workflow Test
# This script tests the complete deployment pipeline

set -e

echo "=============================================="
echo "🧪 MediWatch End-to-End CI/CD Test"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "\n${BLUE}▶ Test: $test_name${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo -e "\n${YELLOW}📋 Phase 1: Pre-Deployment Checks${NC}"
echo "=============================================="

# Test 1: Kubernetes connection
run_test "Kubernetes cluster accessible" \
    "kubectl cluster-info &> /dev/null"

# Test 2: Namespace exists
run_test "MediWatch namespace exists" \
    "kubectl get namespace mediwatch &> /dev/null"

# Test 3: Check current deployments
run_test "API deployment exists" \
    "kubectl get deployment mediwatch-api -n mediwatch &> /dev/null"

# Get current state
echo -e "\n${YELLOW}📊 Current State:${NC}"
CURRENT_PODS=$(kubectl get pods -n mediwatch -l app=mediwatch-api -o name | wc -l | tr -d ' ')
CURRENT_REVISION=$(kubectl rollout history deployment/mediwatch-api -n mediwatch | tail -1 | awk '{print $1}')
echo "• API Pods: $CURRENT_PODS"
echo "• Current Revision: $CURRENT_REVISION"

echo -e "\n${YELLOW}📋 Phase 2: Service Health Checks${NC}"
echo "=============================================="

# Test 4: API health
run_test "API health endpoint responds" \
    "curl -sf http://localhost/health | grep -q 'healthy'"

# Test 5: API model loaded
run_test "API model is loaded" \
    "curl -sf http://localhost/health | grep -q '\"model_loaded\":true'"

# Test 6: Airflow accessible
run_test "Airflow UI accessible" \
    "curl -sf http://localhost:8080/health &> /dev/null"

# Test 7: MLflow accessible (via port-forward)
run_test "MLflow accessible" \
    "curl -sf http://localhost:5000 &> /dev/null"

# Test 8: Evidently accessible (via port-forward)
run_test "Evidently health endpoint" \
    "curl -sf http://localhost:8800/health | grep -q 'healthy'"

echo -e "\n${YELLOW}📋 Phase 3: API Functionality Tests${NC}"
echo "=============================================="

# Test 9: API prediction endpoint
echo -e "\n${BLUE}▶ Test: API prediction endpoint${NC}"
PREDICTION_RESPONSE=$(curl -sf http://localhost/predict \
  -H "Content-Type: application/json" \
  -d '{
    "race": "Caucasian",
    "gender": "Female",
    "age": "[60-70)",
    "time_in_hospital": 3,
    "num_lab_procedures": 50,
    "num_procedures": 1,
    "num_medications": 15,
    "number_outpatient": 0,
    "number_emergency": 0,
    "number_inpatient": 0,
    "diag_1": 250.83,
    "diag_2": 250.01,
    "diag_3": 255,
    "number_diagnoses": 9,
    "max_glu_serum": "None",
    "A1Cresult": "None",
    "change": "Ch",
    "diabetesMed": "Yes"
  }')

if echo "$PREDICTION_RESPONSE" | grep -q "prediction"; then
    echo -e "${GREEN}✅ PASSED${NC}"
    echo "  Prediction: $(echo $PREDICTION_RESPONSE | python3 -c 'import sys, json; print(json.load(sys.stdin)["prediction"])' 2>/dev/null || echo 'N/A')"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED${NC}"
    ((TESTS_FAILED++))
fi

echo -e "\n${YELLOW}📋 Phase 4: Deployment Pipeline Test${NC}"
echo "=============================================="

echo -e "\n${BLUE}This phase simulates a code change and deployment.${NC}"
echo -e "${YELLOW}We'll trigger a rolling restart to simulate CI/CD.${NC}"

read -p "Proceed with deployment test? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    
    # Test 10: Trigger rolling restart
    echo -e "\n${BLUE}▶ Test: Trigger rolling restart${NC}"
    if kubectl rollout restart deployment/mediwatch-api -n mediwatch &> /dev/null; then
        echo -e "${GREEN}✅ Rolling restart triggered${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Failed to trigger restart${NC}"
        ((TESTS_FAILED++))
    fi
    
    # Test 11: Monitor rollout
    echo -e "\n${BLUE}▶ Test: Monitor rollout progress${NC}"
    echo "Waiting for rollout to complete (max 120s)..."
    if timeout 120 kubectl rollout status deployment/mediwatch-api -n mediwatch; then
        echo -e "${GREEN}✅ Rollout completed successfully${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Rollout did not complete in time${NC}"
        ((TESTS_FAILED++))
    fi
    
    # Test 12: Verify new pods
    echo -e "\n${BLUE}▶ Test: Verify new pods are running${NC}"
    sleep 5
    NEW_PODS=$(kubectl get pods -n mediwatch -l app=mediwatch-api -o name | wc -l | tr -d ' ')
    NEW_REVISION=$(kubectl rollout history deployment/mediwatch-api -n mediwatch | tail -1 | awk '{print $1}')
    
    if [ "$NEW_PODS" -ge "$CURRENT_PODS" ] && [ "$NEW_REVISION" -gt "$CURRENT_REVISION" ]; then
        echo -e "${GREEN}✅ New pods deployed${NC}"
        echo "  Old Revision: $CURRENT_REVISION → New Revision: $NEW_REVISION"
        echo "  Pods: $CURRENT_PODS → $NEW_PODS"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Pod deployment issue${NC}"
        ((TESTS_FAILED++))
    fi
    
    # Test 13: Verify API still works after deployment
    echo -e "\n${BLUE}▶ Test: API works after deployment${NC}"
    sleep 3
    if curl -sf http://localhost/health | grep -q "healthy"; then
        echo -e "${GREEN}✅ API healthy after deployment${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ API not responding after deployment${NC}"
        ((TESTS_FAILED++))
    fi
    
else
    echo -e "${YELLOW}⏭️  Skipping deployment test${NC}"
fi

echo -e "\n${YELLOW}📋 Phase 5: Monitoring & Observability${NC}"
echo "=============================================="

# Test 14: Check logs
echo -e "\n${BLUE}▶ Test: Pod logs accessible${NC}"
if kubectl logs -n mediwatch -l app=mediwatch-api --tail=5 &> /dev/null; then
    echo -e "${GREEN}✅ Logs accessible${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Cannot access logs${NC}"
    ((TESTS_FAILED++))
fi

# Test 15: Check HPA
echo -e "\n${BLUE}▶ Test: Horizontal Pod Autoscaler configured${NC}"
if kubectl get hpa mediwatch-api-hpa -n mediwatch &> /dev/null; then
    echo -e "${GREEN}✅ HPA configured${NC}"
    HPA_STATUS=$(kubectl get hpa mediwatch-api-hpa -n mediwatch -o jsonpath='{.status.currentReplicas}/{.spec.maxReplicas}')
    echo "  Current/Max Replicas: $HPA_STATUS"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ HPA not found${NC}"
    ((TESTS_FAILED++))
fi

# Test 16: Evidently reports
echo -e "\n${BLUE}▶ Test: Evidently can list reports${NC}"
if curl -sf http://localhost:8800/reports | grep -q "reports"; then
    echo -e "${GREEN}✅ Evidently reports endpoint working${NC}"
    REPORT_COUNT=$(curl -sf http://localhost:8800/reports | python3 -c 'import sys, json; print(len(json.load(sys.stdin)["reports"]))' 2>/dev/null || echo '0')
    echo "  Reports available: $REPORT_COUNT"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Cannot access Evidently reports${NC}"
    ((TESTS_FAILED++))
fi

# Final Report
echo -e "\n=============================================="
echo -e "${YELLOW}📊 Test Results Summary${NC}"
echo "=============================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo -e "Total Tests:  $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! System is fully operational.${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Review the output above.${NC}"
    exit 1
fi
