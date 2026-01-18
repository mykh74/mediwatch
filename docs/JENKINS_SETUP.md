# Jenkins CI/CD Setup for MediWatch

This guide provides complete instructions for setting up Jenkins CI/CD pipeline for the MediWatch project.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Jenkins Installation](#jenkins-installation)
4. [Jenkins Configuration](#jenkins-configuration)
5. [Pipeline Setup](#pipeline-setup)
6. [Remote Triggering](#remote-triggering)
7. [Airflow Integration](#airflow-integration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Jenkins CI/CD pipeline automates:
- **Building**: Docker image creation with model artifacts
- **Testing**: API health checks and endpoint validation
- **Deployment**: Docker or Kubernetes deployment
- **Remote Triggering**: API-based triggering from Airflow or other systems

**Pipeline Stages**:
1. Initialization & Validation
2. Docker Image Build
3. Automated Testing
4. Registry Push (optional)
5. Deployment (Docker or Kubernetes)
6. Smoke Tests

---

## Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL
- **RAM**: Minimum 4GB, recommended 8GB
- **Docker**: Version 20.10+
- **Java**: JDK 11 or 17 (for Jenkins)

### Software Requirements
```bash
# Check Docker
docker --version  # Should be 20.10+

# Check Java
java -version  # Should be 11 or 17

# For Kubernetes deployment (optional)
kubectl version --client
```

---

## Jenkins Installation

### Option 1: Docker Installation (Recommended)

**1. Create Jenkins Docker Compose File**

We've provided a complete setup in `ci-cd/docker-compose.jenkins.yml`.

**2. Start Jenkins**

```bash
# From project root
cd ci-cd
docker-compose -f docker-compose.jenkins.yml up -d
```

**3. Access Jenkins**

- URL: http://localhost:8080
- Wait ~1 minute for startup

**4. Get Initial Admin Password**

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Copy this password for first-time setup.

### Option 2: Native Installation

#### macOS
```bash
# Install with Homebrew
brew install jenkins-lts

# Start Jenkins
brew services start jenkins-lts
```

#### Ubuntu/Debian
```bash
# Add Jenkins repository
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'

# Install Jenkins
sudo apt update
sudo apt install jenkins

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

#### Access Initial Password (Native)
```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

---

## Jenkins Configuration

### 1. Initial Setup Wizard

1. **Navigate to**: http://localhost:8080
2. **Enter**: Initial admin password
3. **Select**: "Install suggested plugins"
4. **Create**: Admin user account
   - Username: `admin`
   - Password: (your secure password)
   - Email: your@email.com
5. **Confirm**: Jenkins URL (http://localhost:8080/)

### 2. Install Required Plugins

Navigate to: **Manage Jenkins → Manage Plugins → Available**

Install these plugins:
- ✅ **Docker Pipeline** - Docker build/run support
- ✅ **Git** - Source code management
- ✅ **Pipeline** - Pipeline as code
- ✅ **Credentials Binding** - Secure credential management
- ✅ **Kubernetes** (optional) - For K8s deployment
- ✅ **Build Authorization Token Root** - For remote triggering

After installing, click **"Restart Jenkins"**.

### 3. Configure Docker Access

The Jenkins container needs Docker access:

**For Docker-based Jenkins** (already configured in our docker-compose):
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock  # Docker socket
```

**For Native Jenkins**:
```bash
# Add Jenkins user to Docker group
sudo usermod -aG docker jenkins

# Restart Jenkins
sudo systemctl restart jenkins
```

### 4. Set Up Credentials

Navigate to: **Manage Jenkins → Manage Credentials → (global) → Add Credentials**

#### Required Credentials:

**a) Docker Hub Credentials** (if pushing to registry)
- Kind: `Username with password`
- ID: `docker-hub-credentials`
- Username: Your Docker Hub username
- Password: Your Docker Hub password or token
- Description: "Docker Hub Credentials"

**b) MLflow Tracking URI** (optional)
- Kind: `Secret text`
- Secret: `http://localhost:5000` (or your MLflow URL)
- ID: `mlflow-tracking-uri`
- Description: "MLflow Tracking Server URL"

**c) Docker Registry URL** (optional)
- Kind: `Secret text`
- Secret: `docker.io` (or your private registry)
- ID: `docker-registry-url`
- Description: "Docker Registry URL"

**d) Kubeconfig** (if using Kubernetes)
- Kind: `Secret file`
- File: Upload your kubeconfig file
- ID: `kubeconfig`
- Description: "Kubernetes Config"

---

## Pipeline Setup

### 1. Create New Pipeline Job

1. **Click**: "New Item" in Jenkins dashboard
2. **Name**: `mediwatch-ci-cd`
3. **Type**: "Pipeline"
4. **Click**: "OK"

### 2. Configure Pipeline

**General Section**:
- ✅ Check "This project is parameterized"
- Add parameters:
  - `DEPLOY_MODE`: Choice parameter (docker, kubernetes)
  - `RUN_TESTS`: Boolean parameter (default: true)
  - `FORCE_REBUILD`: Boolean parameter (default: false)

**Build Triggers**:
- ✅ Check "Trigger builds remotely"
- Authentication Token: `mediwatch-build-token`
  (Save this - you'll need it for remote triggering)

**Pipeline Section**:
- Definition: "Pipeline script from SCM"
- SCM: "Git"
- Repository URL: `/Users/michaelkuzmyn/projects/ik/MediWatch` (or your Git URL)
- Branch: `*/main` or `*/master`
- Script Path: `Jenkinsfile`

**Or use "Pipeline script" and paste** the Jenkinsfile content directly.

### 3. Save and Test

Click **"Save"** then **"Build Now"** to test the pipeline.

---

## Remote Triggering

Jenkins can be triggered remotely via HTTP API for integration with Airflow or other systems.

### Method 1: Using Authentication Token

**Trigger URL Format**:
```
http://JENKINS_URL/job/JOB_NAME/buildWithParameters?token=TOKEN
```

**Example**:
```bash
# Basic trigger
curl -X POST "http://localhost:8080/job/mediwatch-ci-cd/buildWithParameters?token=mediwatch-build-token"

# With parameters
curl -X POST "http://localhost:8080/job/mediwatch-ci-cd/buildWithParameters?token=mediwatch-build-token&DEPLOY_MODE=docker&RUN_TESTS=true"
```

### Method 2: Using User Credentials

For better security, use user authentication:

```bash
# With username and API token
curl -X POST \
  -u admin:YOUR_API_TOKEN \
  "http://localhost:8080/job/mediwatch-ci-cd/buildWithParameters?DEPLOY_MODE=docker"
```

**Generate API Token**:
1. Click your username (top-right) → Configure
2. Scroll to "API Token" section
3. Click "Add new Token"
4. Copy the generated token

### Method 3: Using Python (for Airflow)

We've provided a Python script for easy integration:

```python
# See: ci-cd/scripts/trigger_jenkins.py

from ci-cd.scripts.trigger_jenkins import trigger_jenkins_build

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

print(f"Triggered build: {build_number}")
```

---

## Airflow Integration

### 1. Install Jenkins Provider (if needed)

```bash
pip install apache-airflow-providers-jenkins
```

### 2. Configure Airflow Connection

In Airflow UI: **Admin → Connections → Add Connection**

- Conn ID: `jenkins_default`
- Conn Type: `HTTP`
- Host: `localhost`
- Port: `8080`
- Login: `admin` (Jenkins username)
- Password: (Your Jenkins API token)

### 3. Use in Airflow DAG

```python
from airflow.providers.http.operators.http import SimpleHttpOperator

# Add to your DAG
trigger_jenkins = SimpleHttpOperator(
    task_id='trigger_jenkins_build',
    http_conn_id='jenkins_default',
    endpoint='/job/mediwatch-ci-cd/buildWithParameters',
    method='POST',
    data={
        'token': 'mediwatch-build-token',
        'DEPLOY_MODE': 'docker',
        'RUN_TESTS': 'true'
    },
    dag=dag
)
```

**Or use our helper script**:

```python
from airflow.operators.python import PythonOperator
import sys
sys.path.append('/path/to/MediWatch')
from ci_cd.scripts.trigger_jenkins import trigger_jenkins_build

def trigger_build():
    return trigger_jenkins_build(
        jenkins_url="http://localhost:8080",
        job_name="mediwatch-ci-cd",
        token="mediwatch-build-token",
        parameters={"DEPLOY_MODE": "docker"}
    )

trigger_task = PythonOperator(
    task_id='trigger_jenkins',
    python_callable=trigger_build,
    dag=dag
)
```

---

## Pipeline Usage

### Build Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `DEPLOY_MODE` | Choice | docker | Target: docker or kubernetes |
| `RUN_TESTS` | Boolean | true | Run API tests before deployment |
| `FORCE_REBUILD` | Boolean | false | Force rebuild even if image exists |
| `CUSTOM_TAG` | String | (empty) | Custom Docker tag (uses build number if empty) |

### Manual Build

1. Navigate to job: http://localhost:8080/job/mediwatch-ci-cd/
2. Click "Build with Parameters"
3. Select options
4. Click "Build"

### View Build Output

1. Click on build number (e.g., "#1")
2. Click "Console Output"
3. Monitor real-time logs

### Check Deployment

After successful build:

**Docker Mode**:
```bash
# Check running container
docker ps | grep mediwatch-api

# View logs
docker logs mediwatch-api

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

**Kubernetes Mode**:
```bash
# Check pods
kubectl get pods -n mediwatch

# View logs
kubectl logs -f deployment/mediwatch-api -n mediwatch

# Check service
kubectl get service -n mediwatch
```

---

## Environment Variables

Configure these in Jenkins pipeline or as environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCKER_REGISTRY` | Docker registry URL | docker.io |
| `IMAGE_NAME` | Docker image name | mediwatch-api |
| `MLFLOW_TRACKING_URI` | MLflow server URL | http://localhost:5000 |
| `MODEL_NAME` | Model name in registry | mediwatch_readmission_classifier |
| `MODEL_STAGE` | Model stage | Production |
| `NAMESPACE` | Kubernetes namespace | mediwatch |

---

## Security Best Practices

### 1. Use API Tokens
Never use passwords directly. Always use Jenkins API tokens.

### 2. Secure Credentials
Store all sensitive data in Jenkins Credentials store.

### 3. Network Security
```bash
# For production, use HTTPS
# Configure Jenkins reverse proxy with nginx/Apache

# Example nginx config:
server {
    listen 443 ssl;
    server_name jenkins.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Restrict Remote Triggering
Enable "Trigger builds remotely" only for specific jobs, use strong tokens.

---

## Troubleshooting

### Issue: "Permission denied" for Docker

**Solution**:
```bash
# Add Jenkins to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# Or for Docker-based Jenkins, check docker.sock mount
docker exec jenkins ls -l /var/run/docker.sock
```

### Issue: Jenkins can't access MLflow

**Solution**:
```bash
# Check network connectivity
docker exec jenkins curl -I http://host.docker.internal:5000

# For Docker-based Jenkins, use host.docker.internal
# Update credentials: mlflow-tracking-uri → http://host.docker.internal:5000
```

### Issue: Build fails at Docker push

**Solution**:
```bash
# Verify Docker Hub credentials
docker login

# Check credentials in Jenkins
# Manage Jenkins → Manage Credentials → docker-hub-credentials

# Try manual push
docker tag mediwatch-api:latest yourusername/mediwatch-api:latest
docker push yourusername/mediwatch-api:latest
```

### Issue: Kubernetes deployment fails

**Solution**:
```bash
# Verify kubectl works
kubectl get nodes

# Check kubeconfig credential in Jenkins
# Ensure context is set correctly

# Test deployment manually
kubectl apply -f kubernetes/api-deployment.yaml
```

### Issue: Remote trigger returns 403

**Solution**:
- Verify token matches in job configuration
- Check "Trigger builds remotely" is enabled
- Try with user credentials instead
- Install "Build Authorization Token Root" plugin

### Issue: Build fails with "No such file or directory"

**Solution**:
```bash
# Ensure Jenkinsfile is in project root
ls -la Jenkinsfile

# Check Git repository is correctly configured
# Verify branch name (main vs master)

# Check file paths in Jenkinsfile
# All paths should be relative to project root
```

---

## Monitoring and Logs

### Jenkins Logs

**Docker-based**:
```bash
docker logs jenkins
docker logs -f jenkins  # Follow logs
```

**Native**:
```bash
sudo tail -f /var/log/jenkins/jenkins.log
```

### Build History

- Dashboard shows recent builds
- Green = success, Red = failure
- Click build number for detailed logs

### Email Notifications (Optional)

Configure in Jenkins:
1. **Manage Jenkins → Configure System**
2. **E-mail Notification** section
3. Add SMTP server details
4. Test email configuration

Add to Jenkinsfile:
```groovy
post {
    failure {
        emailext(
            subject: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: "Check console output: ${env.BUILD_URL}",
            to: "team@mediwatch.com"
        )
    }
}
```

---

## Advanced Configuration

### Parallel Builds

Modify Jenkinsfile to run tests in parallel:

```groovy
stage('Tests') {
    parallel {
        stage('Unit Tests') {
            steps { sh 'pytest tests/unit' }
        }
        stage('Integration Tests') {
            steps { sh 'pytest tests/integration' }
        }
    }
}
```

### Multi-Branch Pipeline

For multiple Git branches:
1. Create "Multibranch Pipeline" instead of "Pipeline"
2. Configure Git repository
3. Jenkins automatically creates jobs for each branch

### Scheduled Builds

Add to pipeline:
```groovy
triggers {
    cron('H 2 * * *')  // Build daily at 2 AM
}
```

---

## Quick Reference

### Essential Commands

```bash
# Start Jenkins (Docker)
docker-compose -f ci-cd/docker-compose.jenkins.yml up -d

# Stop Jenkins
docker-compose -f ci-cd/docker-compose.jenkins.yml down

# View Jenkins logs
docker logs -f jenkins

# Trigger build
curl -X POST "http://localhost:8080/job/mediwatch-ci-cd/buildWithParameters?token=mediwatch-build-token&DEPLOY_MODE=docker"

# Check deployed API
curl http://localhost:8000/health

# View deployed container
docker ps | grep mediwatch-api
```

### Important URLs

- Jenkins Dashboard: http://localhost:8080
- MediWatch API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MLflow UI: http://localhost:5000

---

## Next Steps

1. ✅ Complete Jenkins setup
2. ✅ Test manual build
3. ✅ Test remote triggering
4. ✅ Integrate with Airflow
5. ✅ Configure email notifications (optional)
6. ✅ Set up scheduled builds (optional)
7. ✅ Document deployment process

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review Jenkins console output
- Check Docker/Kubernetes logs
- Refer to main project documentation

**Jenkins Documentation**: https://www.jenkins.io/doc/
**Docker Documentation**: https://docs.docker.com/
**Kubernetes Documentation**: https://kubernetes.io/docs/
