# Custom Jenkins Image with kubectl and Docker CLI

This directory contains a custom Jenkins Docker image that includes:
- Jenkins LTS (latest)
- Docker CLI (for building and managing containers)
- kubectl (for Kubernetes deployments)
- Pre-installed Jenkins plugins (Git, Pipeline, Docker, Kubernetes)

## Building the Image

From the project root directory, run:

```bash
docker build -t jenkins-with-kubectl -f ci-cd/jenkins/Dockerfile .
```

**Build time**: ~5-10 minutes depending on your internet connection

## Deploying the New Jenkins Container

### Step 1: Stop and Remove Existing Jenkins

```bash
# Stop the current Jenkins container
docker stop jenkins

# Remove the container (keeps the data volume)
docker rm jenkins
```

**Note**: Your Jenkins data (jobs, configurations, credentials) is preserved in the `jenkins_home` Docker volume.

### Step 2: Start New Jenkins with Custom Image

```bash
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins-with-kubectl
```

### Step 3: Verify Installation

Wait ~30 seconds for Jenkins to start, then check:

```bash
# Check Jenkins is running
docker ps | grep jenkins

# Verify Docker CLI is available
docker exec jenkins docker --version

# Verify kubectl is available
docker exec jenkins kubectl version --client
```

Expected output:
```
Docker version 29.x.x, build xxxxx
Client Version: v1.x.x
```

## Accessing Jenkins

1. Open browser: http://localhost:8080
2. Your existing jobs and configurations should be intact
3. Credentials should be preserved (GitHub PAT, etc.)

## Testing Kubernetes Deployment

Once Jenkins is running with the new image:

1. Navigate to: http://localhost:8080/job/mediwatch-ci-cd/
2. Click "Build with Parameters"
3. Set `DEPLOY_MODE` to `kubernetes`
4. Click "Build"

**Prerequisites for K8s deployment**:
- Kubernetes cluster must be running (minikube, kind, EKS, GKE, AKS)
- kubeconfig must be accessible from Jenkins container
- For local testing with minikube:
  ```bash
  # Copy kubeconfig into Jenkins
  docker exec jenkins mkdir -p /var/jenkins_home/.kube
  docker cp ~/.kube/config jenkins:/var/jenkins_home/.kube/config
  docker exec jenkins chown jenkins:jenkins /var/jenkins_home/.kube/config
  ```

## Updating the Image

To rebuild with updates:

```bash
# Rebuild the image
docker build -t jenkins-with-kubectl -f ci-cd/jenkins/Dockerfile .

# Stop current Jenkins
docker stop jenkins && docker rm jenkins

# Start with new image
docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins-with-kubectl
```

## Troubleshooting

### Jenkins won't start
```bash
# Check logs
docker logs jenkins

# Common issue: Port already in use
lsof -i :8080
# Kill the process using port 8080, then restart Jenkins
```

### kubectl not working
```bash
# Verify kubectl is installed
docker exec jenkins kubectl version --client

# Check kubeconfig
docker exec jenkins ls -la /var/jenkins_home/.kube/
```

### Docker commands fail
```bash
# Verify Docker socket is mounted
docker exec jenkins ls -la /var/run/docker.sock

# Check Docker CLI
docker exec jenkins docker ps
```

## Image Details

**Base Image**: jenkins/jenkins:lts  
**Additional Tools**:
- Docker CLI (29.x)
- kubectl (latest stable)

**Pre-installed Plugins**:
- git
- workflow-aggregator (Pipeline)
- docker-workflow
- kubernetes
- kubernetes-cli

**Size**: ~800MB (base Jenkins) + ~200MB (Docker + kubectl) = ~1GB total

## Security Notes

1. **Docker Socket Access**: The Jenkins container has access to the host Docker daemon via `/var/run/docker.sock`. This gives Jenkins full control over Docker on the host.

2. **Kubernetes Access**: kubectl will use the kubeconfig from `/var/jenkins_home/.kube/config`. Ensure this config has appropriate RBAC permissions.

3. **Production Recommendations**:
   - Use Jenkins agents instead of running builds on the master
   - Implement proper RBAC for Kubernetes
   - Use secrets management (HashiCorp Vault, AWS Secrets Manager)
   - Enable Jenkins security and authentication

## Next Steps

After successful deployment:

1. ✅ Verify Jenkins is accessible at http://localhost:8080
2. ✅ Check that existing jobs are intact
3. ✅ Verify Docker CLI works: `docker exec jenkins docker ps`
4. ✅ Verify kubectl works: `docker exec jenkins kubectl version --client`
5. ✅ Configure Kubernetes cluster access (if needed)
6. ✅ Run Build #15 with `DEPLOY_MODE=kubernetes`

## Rollback

If you need to roll back to the standard Jenkins image:

```bash
docker stop jenkins && docker rm jenkins

docker run -d \
  --name jenkins \
  --restart=unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

Your data will be preserved as it's stored in the `jenkins_home` volume.
