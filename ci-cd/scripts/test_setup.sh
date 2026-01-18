#!/bin/bash
#
# MediWatch CI/CD Test Script
# Tests the complete Jenkins CI/CD implementation
#

set -e

echo "========================================="
echo "MediWatch CI/CD Test Suite"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

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
}

# Test 1: Docker
echo "Test 1: Docker Installation"
if docker --version > /dev/null 2>&1; then
    test_passed "Docker is installed"
    
    if docker info > /dev/null 2>&1; then
        test_passed "Docker is running"
    else
        test_failed "Docker is not running - please start Docker Desktop"
        echo ""
        echo "To fix: Start Docker Desktop application"
        exit 1
    fi
else
    test_failed "Docker is not installed"
    exit 1
fi
echo ""

# Test 2: Project structure
echo "Test 2: Project Structure"
REQUIRED_FILES=(
    "Jenkinsfile"
    "ci-cd/docker-compose.jenkins.yml"
    "ci-cd/scripts/start_jenkins.sh"
    "ci-cd/scripts/trigger_jenkins.py"
    "api/Dockerfile"
    "api/main.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        test_passed "Found $file"
    else
        test_failed "Missing $file"
    fi
done
echo ""

# Test 3: Python environment
echo "Test 3: Python Environment"
if python3 --version > /dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    test_passed "Python is installed: $PYTHON_VERSION"
    
    # Check for requests library
    if python3 -c "import requests" 2>/dev/null; then
        test_passed "requests library is available"
    else
        test_warning "requests library not found (needed for trigger script)"
        echo "  Install with: pip install requests"
    fi
else
    test_failed "Python 3 is not installed"
fi
echo ""

# Test 4: Check if Jenkins is already running
echo "Test 4: Jenkins Status"
if docker ps | grep -q jenkins; then
    test_passed "Jenkins container is running"
    JENKINS_RUNNING=true
    
    # Check if accessible
    sleep 2
    if curl -s http://localhost:8080/login > /dev/null 2>&1; then
        test_passed "Jenkins is accessible at http://localhost:8080"
    else
        test_warning "Jenkins container running but not accessible yet"
        echo "  Wait a moment and check http://localhost:8080"
    fi
else
    echo "  Jenkins is not running"
    JENKINS_RUNNING=false
fi
echo ""

# Test 5: Docker Compose file
echo "Test 5: Jenkins Docker Compose"
if [ -f "ci-cd/docker-compose.jenkins.yml" ]; then
    if docker-compose -f ci-cd/docker-compose.jenkins.yml config > /dev/null 2>&1; then
        test_passed "Docker Compose configuration is valid"
    else
        test_failed "Docker Compose configuration has errors"
    fi
else
    test_failed "docker-compose.jenkins.yml not found"
fi
echo ""

# Test 6: Script permissions
echo "Test 6: Script Permissions"
if [ -x "ci-cd/scripts/start_jenkins.sh" ]; then
    test_passed "start_jenkins.sh is executable"
else
    test_warning "start_jenkins.sh is not executable"
    echo "  Fix with: chmod +x ci-cd/scripts/start_jenkins.sh"
fi

if [ -x "ci-cd/scripts/trigger_jenkins.py" ]; then
    test_passed "trigger_jenkins.py is executable"
else
    test_warning "trigger_jenkins.py is not executable"
    echo "  Fix with: chmod +x ci-cd/scripts/trigger_jenkins.py"
fi
echo ""

# Test 7: API Docker build
echo "Test 7: API Docker Build (quick validation)"
if docker build -f api/Dockerfile -t mediwatch-api:test --target base . > /tmp/docker-build.log 2>&1; then
    test_passed "API Dockerfile builds successfully"
else
    test_failed "API Dockerfile has build errors"
    echo "  Check logs: cat /tmp/docker-build.log"
fi
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "========================================="
    
    if [ "$JENKINS_RUNNING" = false ]; then
        echo "1. Start Jenkins:"
        echo "   cd ci-cd && ./scripts/start_jenkins.sh"
        echo ""
        echo "2. Access Jenkins at http://localhost:8080"
        echo ""
        echo "3. Configure the pipeline:"
        echo "   - Follow docs/JENKINS_SETUP.md"
        echo "   - Create 'mediwatch-ci-cd' job"
        echo "   - Point to Jenkinsfile"
        echo ""
        echo "4. Test remote trigger:"
        echo "   python ci-cd/scripts/trigger_jenkins.py --help"
    else
        echo "1. Access Jenkins at http://localhost:8080"
        echo ""
        echo "2. If not configured yet, follow docs/JENKINS_SETUP.md"
        echo ""
        echo "3. Test remote trigger:"
        echo "   python ci-cd/scripts/trigger_jenkins.py \\"
        echo "     --job mediwatch-ci-cd \\"
        echo "     --token mediwatch-build-token \\"
        echo "     --deploy-mode docker"
    fi
    
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please fix the issues above.${NC}"
    exit 1
fi
