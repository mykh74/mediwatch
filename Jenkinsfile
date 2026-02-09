/**
 * MediWatch CI/CD Pipeline
 * 
 * This Jenkins pipeline automates:
 * - Docker image building
 * - API testing
 * - Deployment to Kubernetes (or Docker)
 * - Model validation
 */

pipeline {
    agent any
    
    environment {
        // Docker Configuration
        DOCKER_API_VERSION = '1.43'
        DOCKER_REGISTRY = 'localhost'
        IMAGE_NAME = 'mediwatch-api'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        
        // MLflow Configuration
        MLFLOW_TRACKING_URI = 'http://host.docker.internal:5000'
        MODEL_NAME = 'mediwatch_readmission_classifier'
        MODEL_STAGE = 'Production'
        
        // Kubernetes Configuration (optional)
        NAMESPACE = 'mediwatch'
        
        // Deployment Mode: 'docker' or 'kubernetes'
        DEPLOY_MODE = "${params.DEPLOY_MODE ?: 'kubernetes'}"
    }
    
    parameters {
        choice(
            name: 'DEPLOY_MODE',
            choices: ['kubernetes', 'docker'],
            description: 'Deployment target: docker (local/docker-compose) or kubernetes'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run API tests before deployment'
        )
        booleanParam(
            name: 'FORCE_REBUILD',
            defaultValue: false,
            description: 'Force rebuild even if image exists'
        )
        string(
            name: 'CUSTOM_TAG',
            defaultValue: '',
            description: 'Custom Docker image tag (leave empty for build number)'
        )
    }
    
    stages {
        stage('Initialization') {
            steps {
                script {
                    echo "========================================="
                    echo "MediWatch CI/CD Pipeline"
                    echo "========================================="
                    echo "Build Number: ${env.BUILD_NUMBER}"
                    echo "Deploy Mode: ${DEPLOY_MODE}"
                    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
                    echo "========================================="
                    
                    // Use custom tag if provided
                    if (params.CUSTOM_TAG) {
                        env.IMAGE_TAG = params.CUSTOM_TAG
                    }
                    
                    // Set full image name
                    env.FULL_IMAGE_NAME = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }
        
        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }
        
        stage('Validate Environment') {
            steps {
                script {
                    echo 'Validating build environment...'
                    sh '''
                        echo "Docker version:"
                        docker --version
                        
                        echo "Current directory:"
                        pwd
                        
                        echo "Directory contents:"
                        ls -la
                        
                        # Check for required files
                        if [ ! -f "api/Dockerfile" ]; then
                            echo "ERROR: api/Dockerfile not found!"
                            exit 1
                        fi
                        
                        if [ ! -f "api/main.py" ]; then
                            echo "ERROR: api/main.py not found!"
                            exit 1
                        fi
                        
                        echo "Environment validation: PASSED"
                    '''
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image: ${FULL_IMAGE_NAME}"
                    sh """
                        docker build \
                            -t ${FULL_IMAGE_NAME} \
                            -t ${IMAGE_NAME}:latest \
                            -f api/Dockerfile \
                            --build-arg MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                            --build-arg MODEL_NAME=${MODEL_NAME} \
                            --build-arg MODEL_STAGE=${MODEL_STAGE} \
                            .
                    """
                    
                    echo "Docker image built successfully!"
                    
                    // List images
                    sh "docker images | grep ${IMAGE_NAME}"
                }
            }
        }
        
        stage('Run Tests') {
            when {
                expression { params.RUN_TESTS == true }
            }
            steps {
                script {
                    echo 'Starting API tests...'
                    
                    // Start container for testing
                    sh """
                        # Stop any existing test container
                        docker rm -f mediwatch-test 2>/dev/null || true
                        
                        # Run container in detached mode
                        docker run -d \
                            --name mediwatch-test \
                            -p 8888:8000 \
                            -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                            ${FULL_IMAGE_NAME}
                        
                        # Wait for container to be ready
                        echo "Waiting for API to be ready..."
                        sleep 10
                        
                        # Check container status
                        docker ps | grep mediwatch-test
                    """
                    
                    // Run health check
                    sh """
                        echo "Testing health endpoint..."
                        docker exec mediwatch-test curl -f http://localhost:8000/health || {
                            echo "Health check failed!"
                            docker logs mediwatch-test
                            exit 1
                        }
                        
                        echo "Testing API docs..."
                        docker exec mediwatch-test curl -f http://localhost:8000/docs || {
                            echo "API docs check failed!"
                            exit 1
                        }
                        
                        echo "All API tests passed!"
                    """
                    
                    // Cleanup test container
                    sh "docker rm -f mediwatch-test"
                }
            }
        }
        
        stage('Push to Registry') {
            when {
                expression { env.DOCKER_REGISTRY != 'localhost' }
            }
            steps {
                script {
                    echo "Pushing image to registry: ${DOCKER_REGISTRY}"
                    withCredentials([usernamePassword(
                        credentialsId: 'docker-hub-credentials',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            echo \${DOCKER_PASS} | docker login ${DOCKER_REGISTRY} -u \${DOCKER_USER} --password-stdin
                            docker push ${FULL_IMAGE_NAME}
                            docker logout ${DOCKER_REGISTRY}
                        """
                    }
                    echo "Image pushed successfully!"
                }
            }
        }
        
        stage('Deploy to Docker') {
            when {
                expression { env.DEPLOY_MODE == 'docker' }
            }
            steps {
                script {
                    echo 'Deploying to Docker...'
                    sh """
                        # Stop existing container
                        docker rm -f mediwatch-api 2>/dev/null || true
                        
                        # Run new container
                        docker run -d \
                            --name mediwatch-api \
                            --restart unless-stopped \
                            -p 8000:8000 \
                            -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                            -e MODEL_NAME=${MODEL_NAME} \
                            -e MODEL_STAGE=${MODEL_STAGE} \
                            -v \$(pwd)/data:/app/data \
                            -v \$(pwd)/mlruns:/app/mlruns \
                            ${FULL_IMAGE_NAME}
                        
                        # Wait for startup
                        sleep 5
                        
                        # Verify deployment
                        docker ps | grep mediwatch-api
                        
                        echo "Checking API health..."
                        docker exec mediwatch-api curl -f http://localhost:8000/health
                        
                        echo "Deployment successful!"
                        echo "API available at: http://localhost:8000"
                        echo "API Docs: http://localhost:8000/docs"
                    """
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            when {
                expression { env.DEPLOY_MODE == 'kubernetes' }
            }
            steps {
                script {
                    echo "Deploying to Kubernetes cluster..."
                    echo "Namespace: ${NAMESPACE}"
                    echo "Image: ${FULL_IMAGE_NAME}"
                    
                    sh """
                        # Verify kubectl access
                        kubectl version --client
                        kubectl cluster-info
                        
                        # Make deployment script executable
                        chmod +x ci-cd/kubernetes/deploy.sh
                        
                        # Run deployment script with image tag
                        ./ci-cd/kubernetes/deploy.sh ${IMAGE_TAG}
                        
                        # Wait for rollout
                        kubectl rollout status deployment/mediwatch-api -n ${NAMESPACE}
                        
                        # Show deployment status
                        kubectl get pods -n ${NAMESPACE}
                        kubectl get services -n ${NAMESPACE}
                        
                        echo "Kubernetes deployment successful!"
                    """
                }
            }
        }
        
        stage('Smoke Test Deployment') {
            steps {
                script {
                    echo 'Running smoke tests on deployed API...'
                    
                    if (env.DEPLOY_MODE == 'docker') {
                        sh """
                            echo "Testing deployed Docker container..."
                            docker exec mediwatch-api curl -f http://localhost:8000/health
                            echo "Smoke test passed!"
                        """
                    } else {
                        echo "Kubernetes smoke test - testing service endpoint..."
                        sh """
                            # Wait for LoadBalancer IP (timeout after 2 minutes)
                            echo "Waiting for service endpoint..."
                            timeout=120
                            elapsed=0
                            
                            while [ \$elapsed -lt \$timeout ]; do
                                EXTERNAL_IP=\$(kubectl get svc mediwatch-api-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
                                if [ -z "\$EXTERNAL_IP" ]; then
                                    EXTERNAL_IP=\$(kubectl get svc mediwatch-api-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
                                fi
                                
                                if [ -n "\$EXTERNAL_IP" ]; then
                                    echo "✓ Service endpoint available: \$EXTERNAL_IP"
                                    
                                    # Test health endpoint
                                    echo "Testing health endpoint..."
                                    curl -f http://\$EXTERNAL_IP/health || {
                                        echo "Health check failed, trying with kubectl port-forward..."
                                        kubectl port-forward -n ${NAMESPACE} svc/mediwatch-api-service 8888:80 &
                                        sleep 5
                                        curl -f http://localhost:8888/health
                                        pkill -f "kubectl port-forward"
                                    }
                                    
                                    echo "✓ Smoke test passed!"
                                    exit 0
                                fi
                                
                                echo "Waiting for LoadBalancer IP... (\$elapsed/\$timeout seconds)"
                                sleep 10
                                elapsed=\$((elapsed + 10))
                            done
                            
                            # If LoadBalancer IP not available, test via port-forward
                            echo "LoadBalancer IP not available, testing via port-forward..."
                            kubectl port-forward -n ${NAMESPACE} svc/mediwatch-api-service 8888:80 &
                            PF_PID=\$!
                            sleep 10
                            
                            curl -f http://localhost:8888/health
                            kill \$PF_PID
                            
                            echo "✓ Smoke test passed (via port-forward)"
                        """
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '========================================='
            echo 'Pipeline completed successfully! ✓'
            echo '========================================='
            echo "Image: ${FULL_IMAGE_NAME}"
            echo "Deployment Mode: ${DEPLOY_MODE}"
            
            script {
                if (env.DEPLOY_MODE == 'docker') {
                    echo "API URL: http://localhost:8000"
                    echo "API Docs: http://localhost:8000/docs"
                }
            }
            
            // Archive build info
            sh """
                cat > build-info.txt <<EOF
Build Number: ${env.BUILD_NUMBER}
Image: ${FULL_IMAGE_NAME}
Deployment Mode: ${DEPLOY_MODE}
Timestamp: \$(date)
Git Commit: ${env.GIT_COMMIT ?: 'N/A'}
EOF
            """
            archiveArtifacts artifacts: 'build-info.txt', fingerprint: true
        }
        
        failure {
            echo '========================================='
            echo 'Pipeline failed! ✗'
            echo '========================================='
            
            script {
                // Collect logs for debugging
                sh """
                    echo "Docker containers:"
                    docker ps -a | grep mediwatch || echo "No containers found"
                    
                    echo "Recent logs:"
                    docker logs mediwatch-api 2>/dev/null || echo "No logs available"
                """
            }
        }
        
        always {
            echo 'Cleaning up...'
            sh """
                # Clean up test containers
                docker rm -f mediwatch-test 2>/dev/null || true
            """
        }
    }
}
