# Jenkins Workflow - Quick Start Guide

## 🚀 Running the Jenkins CI/CD Pipeline

### Step 1: Start Jenkins Container

```bash
# Navigate to project
cd /Users/michaelkuzmyn/projects/ik/MediWatch

# Start Jenkins (choose one method):

# Method A: Using Docker Compose
cd ci-cd
docker-compose -f docker-compose.jenkins.yml up -d

# Method B: Using Docker directly
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /Users/michaelkuzmyn/projects/ik/MediWatch:/workspace \
  jenkins/jenkins:lts

# Wait for Jenkins to start (60-90 seconds)
sleep 60
```

### Step 2: Get Initial Admin Password

```bash
# Get the initial password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Or check logs for the password
docker logs jenkins 2>&1 | grep -A 5 "initial"
```

### Step 3: Access Jenkins Web UI

1. Open your browser: **http://localhost:8080**
2. Enter the initial admin password from Step 2
3. Click "Install suggested plugins" (takes 3-5 minutes)
4. Create admin user:
   - Username: `admin`
   - Password: `admin123` (or your choice)
   - Full name: `Admin`
   - Email: `admin@mediwatch.local`
5. Click "Save and Continue"
6. Keep default Jenkins URL: `http://localhost:8080/`
7. Click "Start using Jenkins"

### Step 4: Create the Pipeline Job

1. Click "New Item"
2. Enter name: `mediwatch-ci-cd`
3. Select "Pipeline"
4. Click "OK"

### Step 5: Configure the Pipeline

In the job configuration:

#### General Tab:
- ✅ Check "This project is parameterized"
- Add these parameters:

**Parameter 1: DEPLOY_MODE**
- Type: Choice Parameter
- Name: `DEPLOY_MODE`
- Choices (one per line):
  ```
  docker
  kubernetes
  ```
- Default: `docker`
- Description: `Deployment target`

**Parameter 2: RUN_TESTS**
- Type: Boolean Parameter
- Name: `RUN_TESTS`
- Default: Checked
- Description: `Run API tests before deployment`

**Parameter 3: FORCE_REBUILD**
- Type: Boolean Parameter
- Name: `FORCE_REBUILD`
- Default: Unchecked
- Description: `Force rebuild Docker image`

**Parameter 4: CUSTOM_TAG**
- Type: String Parameter
- Name: `CUSTOM_TAG`
- Default: `latest`
- Description: `Custom Docker image tag`

#### Pipeline Section:
- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: `/workspace` (the mounted directory)
- Branch Specifier: `*/main` or `*/master`
- Script Path: `Jenkinsfile`

Click **"Save"**

### Step 6: Run the Pipeline

#### Option A: Manual Trigger (UI)

1. Click "Build with Parameters"
2. Select your options:
   - DEPLOY_MODE: `docker`
   - RUN_TESTS: ✅ (checked)
   - FORCE_REBUILD: ☐ (unchecked)
   - CUSTOM_TAG: `latest`
3. Click "Build"
4. Watch the pipeline progress in the Build History
5. Click on the build number to see console output

#### Option B: Remote Trigger (CLI)

```bash
# Using the trigger script
cd /Users/michaelkuzmyn/projects/ik/MediWatch

python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --deploy-mode docker \
  --run-tests true \
  --wait

# Or with custom tag
python ci-cd/scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --deploy-mode docker \
  --run-tests true \
  --tag v1.0.0 \
  --wait
```

#### Option C: API Trigger (curl)

```bash
# Get crumb for CSRF protection
CRUMB=$(curl -s 'http://admin:admin123@localhost:8080/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,":",//crumb)')

# Trigger build
curl -X POST "http://admin:admin123@localhost:8080/job/mediwatch-ci-cd/buildWithParameters" \
  -H "$CRUMB" \
  --data-urlencode "DEPLOY_MODE=docker" \
  --data-urlencode "RUN_TESTS=true" \
  --data-urlencode "FORCE_REBUILD=false" \
  --data-urlencode "CUSTOM_TAG=latest"
```

### Step 7: Monitor the Pipeline

The pipeline has **7 stages**:

1. **Initialization** - Setup environment
2. **Checkout** - Pull code (already mounted)
3. **Validate** - Check files and config
4. **Build** - Build Docker image
5. **Test** - Run API tests
6. **Deploy Docker** - Deploy to Docker
7. **Smoke Test** - Verify deployment

#### Watch Console Output:
```bash
# View build logs
docker logs jenkins -f

# Or in Jenkins UI
# Click build number → Console Output
```

### Step 8: Verify Deployment

After successful build:

```bash
# Check deployed container
docker ps | grep mediwatch

# Test the API
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Check Jenkins build status
open http://localhost:8080/job/mediwatch-ci-cd/
```

---

## 📊 Expected Pipeline Output

### Stage 1: Initialization ✓
```
Loading parameters...
DEPLOY_MODE: docker
RUN_TESTS: true
Environment ready
```

### Stage 2: Checkout ✓
```
Checking workspace: /workspace
Jenkinsfile found
```

### Stage 3: Validate ✓
```
Validating Jenkinsfile...
Checking required files...
✓ api/Dockerfile
✓ requirements.txt
✓ src/
```

### Stage 4: Build ✓
```
Building Docker image: mediwatch-api:latest
Build time: ~2 minutes (with cache)
Image size: ~850MB
```

### Stage 5: Test ✓
```
Starting API container for testing...
Running health check tests...
✓ Health endpoint: PASS
✓ Model info endpoint: PASS
✓ Prediction endpoint: PASS
```

### Stage 6: Deploy ✓
```
Deploying to Docker...
Stopping old container...
Starting new container...
Container: mediwatch-api (port 8000)
```

### Stage 7: Smoke Test ✓
```
Testing deployed service...
✓ Health check: 200 OK
✓ Service responding
Deployment successful!
```

---

## 🐛 Troubleshooting

### Jenkins Won't Start

```bash
# Check Docker is running
docker info

# Check port availability
lsof -i :8080

# Remove old container and restart
docker stop jenkins
docker rm jenkins
# Then run start command again
```

### Can't Access Jenkins UI

```bash
# Check if Jenkins is running
docker ps | grep jenkins

# Check logs
docker logs jenkins

# Verify port mapping
docker port jenkins

# Test connection
curl http://localhost:8080
```

### Build Fails at Docker Build Stage

```bash
# Ensure Docker socket is mounted
docker exec jenkins ls -la /var/run/docker.sock

# Test Docker access from Jenkins
docker exec jenkins docker ps

# If permission denied, restart Jenkins container with proper permissions
```

### Build Fails at Test Stage

```bash
# Ensure MLflow is running
ps aux | grep mlflow

# Check if port 5000 is accessible
curl http://localhost:5000/health

# Restart MLflow if needed
cd /Users/michaelkuzmyn/projects/ik/MediWatch
nohup .venv/bin/mlflow server --host 127.0.0.1 --port 5000 \
  --backend-store-uri sqlite:///mlruns.db \
  --default-artifact-root ./mlruns > mlflow.log 2>&1 &
```

### Pipeline Configuration Not Found

```bash
# Ensure workspace is mounted correctly
docker exec jenkins ls -la /workspace

# Check Jenkinsfile exists
docker exec jenkins cat /workspace/Jenkinsfile | head -20

# If missing, check volume mount in docker run command
```

---

## 🔧 Advanced: Configure Credentials

For production deployments, configure these credentials in Jenkins:

### Docker Registry Credentials
1. Jenkins → Manage Jenkins → Credentials
2. Add Credentials:
   - Kind: Username with password
   - ID: `docker-registry-creds`
   - Username: Your Docker Hub username
   - Password: Your Docker Hub password/token

### Kubernetes Config (if using K8s)
1. Add Credentials:
   - Kind: Secret file
   - ID: `kubeconfig`
   - File: Upload your `~/.kube/config`

### MLflow Token (if authentication enabled)
1. Add Credentials:
   - Kind: Secret text
   - ID: `mlflow-token`
   - Secret: Your MLflow tracking token

---

## 🔄 Integrating with Airflow

To trigger Jenkins from Airflow DAG:

```python
from airflow.operators.python import PythonOperator
import subprocess

def trigger_jenkins_build(**context):
    """Trigger Jenkins CI/CD pipeline"""
    result = subprocess.run([
        "python",
        "/path/to/ci-cd/scripts/trigger_jenkins.py",
        "--job", "mediwatch-ci-cd",
        "--deploy-mode", "docker",
        "--run-tests", "true",
        "--wait"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Jenkins build failed: {result.stderr}")
    
    print(result.stdout)
    return "SUCCESS"

deploy_task = PythonOperator(
    task_id='deploy_via_jenkins',
    python_callable=trigger_jenkins_build,
    dag=dag
)
```

---

## 📈 Performance Tips

### Speed Up Builds

1. **Use Docker layer caching**:
   - Jenkins automatically caches layers
   - First build: ~5 minutes
   - Subsequent builds: ~30 seconds

2. **Skip tests for dev builds**:
   - Set `RUN_TESTS=false` for quick iterations

3. **Parallel builds**:
   - Jenkins supports multiple builds
   - Configure in job settings

### Monitor Resources

```bash
# Check Docker resource usage
docker stats jenkins

# Check disk space
docker system df

# Clean up old images
docker image prune -a
```

---

## ✅ Success Indicators

Your Jenkins workflow is successful when:

- [ ] Jenkins UI accessible at http://localhost:8080
- [ ] Pipeline job created and configured
- [ ] First build completes successfully
- [ ] All 7 stages pass (green checkmarks)
- [ ] API deployed and accessible at port 8000
- [ ] Health checks return 200 OK
- [ ] Container appears in `docker ps`
- [ ] No errors in console output

---

## 📚 Next Steps

After successful Jenkins setup:

1. **Test Remote Triggering**:
   ```bash
   python ci-cd/scripts/trigger_jenkins.py --job mediwatch-ci-cd --wait
   ```

2. **Configure Webhooks** (if using Git):
   - Jenkins → Job → Configure
   - Build Triggers → GitHub hook trigger

3. **Setup Notifications**:
   - Email notifications for build failures
   - Slack integration
   - Status badges

4. **Production Deployment**:
   - Switch DEPLOY_MODE to `kubernetes`
   - Configure kubectl access
   - Test K8s deployment

---

## 🎯 Quick Command Reference

```bash
# Start Jenkins
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /Users/michaelkuzmyn/projects/ik/MediWatch:/workspace \
  jenkins/jenkins:lts

# Get password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# View logs
docker logs -f jenkins

# Restart Jenkins
docker restart jenkins

# Stop Jenkins
docker stop jenkins

# Trigger build
python ci-cd/scripts/trigger_jenkins.py --job mediwatch-ci-cd --wait

# Check deployed API
curl http://localhost:8000/health
```

---

**Ready to run your Jenkins workflow!** 🚀

Open http://localhost:8080 and follow the steps above.
