# CI/CD Directory

This directory contains Jenkins CI/CD pipeline configuration and scripts for the MediWatch project.

## Contents

```
ci-cd/
├── docker-compose.jenkins.yml    # Jenkins Docker Compose setup
├── scripts/
│   ├── start_jenkins.sh          # Quick start script
│   └── trigger_jenkins.py        # Remote build trigger
└── README.md                     # This file
```

## Quick Start

### 1. Start Jenkins

```bash
# Easy way (recommended)
./scripts/start_jenkins.sh

# Or manually
docker-compose -f docker-compose.jenkins.yml up -d
```

### 2. Access Jenkins

- URL: http://localhost:8080
- Get initial password:
  ```bash
  docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
  ```

### 3. Configure Pipeline

Follow the setup guide: [../docs/JENKINS_SETUP.md](../docs/JENKINS_SETUP.md)

## Remote Triggering

### Using Python Script

```bash
# Basic trigger
python scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token \
  --deploy-mode docker

# With monitoring
python scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token \
  --deploy-mode docker \
  --run-tests \
  --wait \
  --monitor
```

### Using curl

```bash
curl -X POST "http://localhost:8080/job/mediwatch-ci-cd/buildWithParameters?token=mediwatch-build-token&DEPLOY_MODE=docker&RUN_TESTS=true"
```

### From Python Code

```python
from ci_cd.scripts.trigger_jenkins import trigger_jenkins_build

build_number = trigger_jenkins_build(
    jenkins_url="http://localhost:8080",
    job_name="mediwatch-ci-cd",
    token="mediwatch-build-token",
    parameters={
        "DEPLOY_MODE": "docker",
        "RUN_TESTS": True
    }
)
```

## Files

### docker-compose.jenkins.yml

Docker Compose configuration for Jenkins with:
- Jenkins LTS
- Docker-in-Docker support
- Project volume mount
- MLflow integration (optional)
- Persistent data storage

### scripts/start_jenkins.sh

Automated Jenkins startup script:
- Validates Docker
- Starts Jenkins container
- Retrieves initial password
- Displays setup instructions

### scripts/trigger_jenkins.py

Remote build trigger with:
- CLI interface
- Python API
- Build monitoring
- Status tracking
- Airflow integration support

## Documentation

- **Complete Setup Guide**: [../docs/JENKINS_SETUP.md](../docs/JENKINS_SETUP.md)
- **CI/CD Summary**: [../docs/CI_CD_SUMMARY.md](../docs/CI_CD_SUMMARY.md)
- **Pipeline Code**: [../Jenkinsfile](../Jenkinsfile)

## Usage Examples

### Start Jenkins
```bash
cd ci-cd
./scripts/start_jenkins.sh
```

### Stop Jenkins
```bash
docker-compose -f docker-compose.jenkins.yml down
```

### View Logs
```bash
docker logs -f jenkins
```

### Trigger Build
```bash
python scripts/trigger_jenkins.py \
  --job mediwatch-ci-cd \
  --token mediwatch-build-token
```

## Integration with Airflow

See [../orchestration/airflow/dags/mediwatch_pipeline_with_cicd.py](../orchestration/airflow/dags/mediwatch_pipeline_with_cicd.py) for DAG example.

## Troubleshooting

### Jenkins won't start
```bash
# Check Docker
docker info

# Check port 8080
lsof -i :8080

# View logs
docker logs jenkins
```

### Can't trigger builds
```bash
# Verify Jenkins is running
curl http://localhost:8080/login

# Check token in job configuration
# Ensure "Trigger builds remotely" is enabled
```

### Docker build fails
```bash
# Check Docker socket mount
docker exec jenkins ls -l /var/run/docker.sock

# Verify project mount
docker exec jenkins ls /workspace/mediwatch
```

For more help, see [../docs/JENKINS_SETUP.md#troubleshooting](../docs/JENKINS_SETUP.md#troubleshooting)

## Requirements

- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum
- 10GB disk space

## Architecture

```
┌─────────────────────────────────────┐
│     Jenkins Container               │
│  ┌───────────────────────────────┐  │
│  │   Jenkins Server (port 8080)  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   Docker Client               │  │
│  │   (via socket mount)          │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   Project Files               │  │
│  │   (/workspace/mediwatch)      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │              │
         │              └─────────────────┐
         │                                │
         ▼                                ▼
┌──────────────────┐          ┌──────────────────┐
│  Docker Daemon   │          │  MLflow Server   │
│  (Host)          │          │  (Optional)      │
└──────────────────┘          └──────────────────┘
```

## Security Notes

- **Credentials**: Store in Jenkins Credentials store
- **Tokens**: Use strong, random tokens
- **Network**: Consider HTTPS for production
- **Updates**: Keep Jenkins and plugins updated

## Support

For issues or questions:
- Check documentation: [../docs/JENKINS_SETUP.md](../docs/JENKINS_SETUP.md)
- Review Jenkinsfile: [../Jenkinsfile](../Jenkinsfile)
- See troubleshooting section above
