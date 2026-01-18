# Testing the Jenkins CI/CD Implementation

This guide walks through testing the complete Jenkins CI/CD setup for MediWatch.

## Prerequisites Check

**Before starting, ensure:**
- ✅ Docker Desktop is installed and running
- ✅ You have at least 4GB RAM available
- ✅ Port 8080 is free (Jenkins)
- ✅ Port 8000 is free (API)

## Test Phase 1: Environment Setup

### 1.1 Start Docker Desktop

```bash
# On macOS: Open Docker Desktop application
# Wait for Docker to start (whale icon in menu bar)

# Verify Docker is running
docker info
```

**Expected**: Docker info displays without errors

### 1.2 Run Setup Test Script

```bash
cd /Users/michaelkuzmyn/projects/ik/MediWatch
./ci-cd/scripts/test_setup.sh
```

**Expected**: All tests pass with green checkmarks

### 1.3 Fix Any Issues

If tests fail, follow the suggestions in the output.

## Test Phase 2: Start Jenkins

### 2.1 Start Jenkins Container

```bash
cd ci-cd
./scripts/start_jenkins.sh
```

**Expected Output**:
```
✓ Docker is running
Starting Jenkins...
Waiting for Jenkins to start...
✓ Jenkins Started Successfully!

🔑 Initial Admin Password:
   [PASSWORD WILL BE SHOWN HERE]

📍 Access Jenkins at: http://localhost:8080
```

**Troubleshooting**:
- If port 8080 is in use: `lsof -i :8080` to find the process
- If container fails: Check logs with `docker logs jenkins`

### 2.2 Access Jenkins UI

1. Open browser: http://localhost:8080
2. **Expected**: Jenkins unlock page

### 2.3 Complete Initial Setup

1. Enter the initial admin password (shown in terminal)
2. Click "Install suggested plugins"
3. Wait for plugins to install (~2-3 minutes)
4. Create admin user:
   - Username: `admin`
   - Password: (choose a password)
   - Full name: `Admin User`
   - Email: your@email.com
5. Keep URL as http://localhost:8080
6. Click "Start using Jenkins"

**Expected**: Jenkins dashboard appears

## Test Phase 3: Configure Pipeline

### 3.1 Create Pipeline Job

1. Click "New Item"
2. Enter name: `mediwatch-ci-cd`
3. Select "Pipeline"
4. Click "OK"

### 3.2 Configure Job

**General Section**:
- ✅ Description: "MediWatch CI/CD Pipeline"

**Build Triggers**:
- ✅ Check "Trigger builds remotely (e.g., from scripts)"
- Authentication Token: `mediwatch-build-token`

**Pipeline Section**:
- Definition: "Pipeline script from SCM"
- SCM: "Git" (or "None" for local testing)
- If using "None":
  - Definition: "Pipeline script"
  - Script: Copy content from `Jenkinsfile`

**For local testing without Git**:
1. Select "Pipeline script" 
2. Copy entire content from `/Users/michaelkuzmyn/projects/ik/MediWatch/Jenkinsfile`
3. Paste into Script field

Click "Save"

### 3.3 Configure Credentials (if needed)

Navigate to: Manage Jenkins → Manage Credentials → (global) → Add Credentials

**Optional credentials**:
- Docker Hub (if pushing images)
- MLflow URL (as secret text)

## Test Phase 4: Manual Build Test

### 4.1 Trigger First Build

1. Go to job page: http://localhost:8080/job/mediwatch-ci-cd/
2. Click "Build with Parameters"
3. Set parameters:
   - DEPLOY_MODE: `docker`
   - RUN_TESTS: `true`
   - Others: leave as default
4. Click "Build"

### 4.2 Monitor Build

1. Click on build number (e.g., "#1")
2. Click "Console Output"
3. Watch the build progress

**Expected stages**:
```
✓ Initialization
✓ Checkout
✓ Validate Environment
✓ Build Docker Image
✓ Run Tests
✓ Deploy to Docker
✓ Smoke Test Deployment
```

**Expected duration**: 3-5 minutes for first build

### 4.3 Verify Success

**In Console Output, look for**:
```
Pipeline completed successfully! ✓
API URL: http://localhost:8000
```

**Verify deployed API**:
```bash
# Check container is running
docker ps | grep mediwatch-api

# Test health endpoint
curl http://localhost:8000/health

# Expected: {"status": "healthy", ...}

# Test API docs
open http://localhost:8000/docs
```

## Test Phase 5: Remote Trigger Test

### 5.1 Test Trigger Script

```bash
cd /Users/michaelkuzmyn/projects/ik/MediWatch

# Test help
python ci-cd/scripts/trigger_jenkins.py --help

# Expected: Help message with all options
```

### 5.2 Trigger Build via Script

```bash
python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token \
  --deploy-mode docker \
  --run-tests
```

**Expected Output**:
```
Triggering Jenkins job: mediwatch-ci-cd
Parameters: {
  "DEPLOY_MODE": "docker",
  "RUN_TESTS": "true",
  "token": "mediwatch-build-token"
}
✓ Build triggered successfully!
Build number: #2
```

### 5.3 Monitor Remote Build

```bash
python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token \
  --deploy-mode docker \
  --wait \
  --monitor
```

**Expected**: Real-time build status updates

## Test Phase 6: API Testing

### 6.1 Test Deployed API

```bash
# Health check
curl http://localhost:8000/health

# Model info
curl http://localhost:8000/model/info

# API documentation
curl http://localhost:8000/docs
```

### 6.2 Make Test Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predict \
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
      "change": "No",
      "diabetesMed": "Yes"
    }
  }'
```

**Expected Response**:
```json
{
  "prediction": 1,
  "probability": 0.75,
  "risk_level": "High",
  "model_version": "1"
}
```

## Test Phase 7: Integration Test (Optional)

### 7.1 Test from Python Code

Create test file: `test_jenkins_integration.py`

```python
from ci_cd.scripts.trigger_jenkins import trigger_jenkins_build

# Trigger build
build_number = trigger_jenkins_build(
    jenkins_url="http://localhost:8080",
    job_name="mediwatch-ci-cd",
    token="mediwatch-build-token",
    parameters={
        "DEPLOY_MODE": "docker",
        "RUN_TESTS": True
    }
)

print(f"Build triggered: #{build_number}")
```

Run test:
```bash
python test_jenkins_integration.py
```

## Test Checklist

Use this checklist to verify all tests pass:

### Environment
- [ ] Docker is installed and running
- [ ] Docker Compose works
- [ ] Python 3 is available
- [ ] requests library is installed

### Jenkins Setup
- [ ] Jenkins container starts
- [ ] Jenkins UI is accessible
- [ ] Initial setup completed
- [ ] Admin user created

### Pipeline Configuration
- [ ] Pipeline job created
- [ ] Jenkinsfile is loaded
- [ ] Build trigger token set
- [ ] Parameters configured

### Build Testing
- [ ] Manual build succeeds
- [ ] Docker image builds
- [ ] Tests pass
- [ ] Deployment succeeds
- [ ] Smoke tests pass

### Remote Triggering
- [ ] Trigger script works
- [ ] Build triggers via API
- [ ] Build monitoring works
- [ ] Status tracking works

### API Testing
- [ ] Container is running
- [ ] Health endpoint responds
- [ ] API docs accessible
- [ ] Predictions work

### Documentation
- [ ] Console output captured
- [ ] Screenshots taken
- [ ] Build artifacts saved

## Troubleshooting

### Issue: Docker not running
```bash
# Start Docker Desktop
open -a Docker
# Wait 30 seconds
docker info
```

### Issue: Port 8080 in use
```bash
# Find process using port
lsof -i :8080
# Kill process or use different port
```

### Issue: Jenkins won't start
```bash
# Check logs
docker logs jenkins

# Restart container
docker restart jenkins

# Or start fresh
docker-compose -f ci-cd/docker-compose.jenkins.yml down
docker-compose -f ci-cd/docker-compose.jenkins.yml up -d
```

### Issue: Build fails at Docker build
```bash
# Check Dockerfile
cat api/Dockerfile

# Try manual build
docker build -t mediwatch-api:test -f api/Dockerfile .

# Check Jenkins Docker access
docker exec jenkins ls -l /var/run/docker.sock
```

### Issue: Remote trigger returns 403
```bash
# Verify token in job config
# Ensure "Trigger builds remotely" is checked
# Try with user authentication instead:

python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --username admin \
  --api-token YOUR_API_TOKEN
```

### Issue: API not responding
```bash
# Check container
docker ps | grep mediwatch-api
docker logs mediwatch-api

# Check if port is accessible
curl -v http://localhost:8000/health

# Restart container
docker restart mediwatch-api
```

## Success Criteria

✅ **All tests pass if**:
1. Jenkins starts and is accessible
2. Pipeline job is configured
3. Manual build succeeds
4. Remote trigger works
5. API is deployed and responds
6. Predictions return valid results

## Next Steps After Testing

1. **Capture Screenshots**:
   - Follow [SCREENSHOTS_GUIDE.md](SCREENSHOTS_GUIDE.md)
   - Document each test phase

2. **Update Documentation**:
   - Add any custom configurations
   - Note any issues encountered

3. **Prepare for Submission**:
   - Ensure all documentation is complete
   - Verify all requirements are met
   - Package project materials

## Test Results Template

```
Test Date: [DATE]
Tester: [NAME]

Environment Setup:        [ ] PASS  [ ] FAIL
Jenkins Startup:          [ ] PASS  [ ] FAIL
Pipeline Configuration:   [ ] PASS  [ ] FAIL
Manual Build:             [ ] PASS  [ ] FAIL
Remote Trigger:           [ ] PASS  [ ] FAIL
API Deployment:           [ ] PASS  [ ] FAIL
API Testing:              [ ] PASS  [ ] FAIL

Notes:
- 
- 

Overall: [ ] PASS  [ ] FAIL
```

---

**Ready to test?** Start with Step 1: Start Docker Desktop! 🚀

For detailed help, see [JENKINS_SETUP.md](../docs/JENKINS_SETUP.md)
