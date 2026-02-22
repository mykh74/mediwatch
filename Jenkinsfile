pipeline {
    agent any
    // agent {
    //     docker { 
    //         image 'dtzar/helm-kubectl:3.12.0' // Use an image with both Helm and Kubectl
    //         //mount docker socket to allow Helm to use the host's Docker daemon for building images (if needed in the future)
    //          args '-u root --entrypoint= -v /var/run/docker.sock:/var/run/docker.sock'  // Run as root to allow Helm to use entrypoint for commands
    //     }
    // }

    environment {
        // Jenkins Credentials Binding

        GITHUB_ACCESS = credentials('github-account-token') // GitHub Personal Access Token for github access, used for Airflow Git Sync
        POSTGRES_APP = credentials('postgres-user-account')
        POSTGRES_ADMIN = credentials('postgres-admin-password')

        // File credential for kubeconfig. Automatically used by kubectl/helm when KUBECONFIG env var is set to the file path provided by Jenkins.
        KUBECONFIG = credentials('local-kube-config') 
    
        DB_HOST = 'postgres-postgresql.default.svc.cluster.local' // Service name for Postgres in Kubernetes
        DB_NAME = 'airflow_db'

    }

    stages {
        stage('Checkout') {
            agent any
            steps {
                checkout scm
            }
        }
        
        stage('Deploy Postgres') {
            agent {
                docker { 
                    image 'dtzar/helm-kubectl:3.12.0' // Use an image with both Helm and Kubectl
                    //mount docker socket to allow Helm to use the host's Docker daemon for building images (if needed in the future)
                    args '-u root --entrypoint= -v ${KUBECONFIG}:${KUBECONFIG}:ro'  // Run as root to allow Helm to use entrypoint for commands
                }
            }
            steps {

                script {
                    // Navigate to the helm directory relative to repo root
                    dir('infrastructure/helm') {
                        sh 'helm repo add bitnami https://charts.bitnami.com/bitnami'
                        sh 'helm repo update'

                        // 1. Fix the localhost mapping inside the secret file (kubernetes doesnt uses 'host.docker.internal' as localhost, but we need to map it for the helm deployment to work)
                        // sh "sed -i 's/127.0.0.1/host.docker.internal/g' ${KUBECONFIG}"

                        // Deploy Postgres using Helm, injecting secrets from Jenkins credentials
                        // Using 'upgrade --install' ensures idempotency
                        
                        sh '''
                            helm upgrade --install postgres bitnami/postgresql \
                                -f postgres-values.yml \
                                --set auth.username=${POSTGRES_APP_USR} \
                                --set auth.password=${POSTGRES_APP_PSW} \
                                --set auth.postgresPassword=${POSTGRES_ADMIN} \
                                --set auth.database=${DB_NAME} \
                                --wait
                        '''
                    }
                }
            }
        }

        stage('Deploy Airflow') {
            agent {
                docker { 
                    image 'dtzar/helm-kubectl:3.12.0' // Use an image with both Helm and Kubectl
                    //mount docker socket to allow Helm to use the host's Docker daemon for building images (if needed in the future)
                    args '-u root --entrypoint= -v ${KUBECONFIG}:${KUBECONFIG}:ro'  // Run as root to allow Helm to use entrypoint for commands
                }
            }
            steps {

                script{
                    // Confirm Github token provides access to the repository by making a simple API call
                    sh '''
                        curl -H "Authorization: token ${GITHUB_ACCESS_PSW}" \
                        -H "Accept: application/vnd.github.v3+json" \
                        https://api.github.com/repos/mykh74/mediwatch \
                        | jq 'has("status") | not'
                    '''
                }

                script{
                    //Generate secret file for Kustomization and load secrets securely that way

                    // Use Kustomize to generate secrets idempotently
                    dir('infrastructure') {
                        // Ensure the namespace exists before creating secrets in it
                        sh 'kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -'

                        // Create .env file for the database secret from Jenkins credentials
                        def dbConnection = 'postgresql://${POSTGRES_APP_USR}:${POSTGRES_APP_PSW}@${DB_HOST}:5432/${DB_NAME}'
                        writeFile file: 'db-secret.env', text: 'connection=${dbConnection}'

                        // Create .env file for the git credentials secret from Jenkins credentials
                        writeFile file: 'git-secret.env', text: '''
                            GIT_SYNC_USERNAME=${GITHUB_ACCESS_USR}
                            GIT_SYNC_PASSWORD=${GITHUB_ACCESS_PSW}
                            GITSYNC_USERNAME=${GITHUB_ACCESS_USR}
                            GITSYNC_PASSWORD=${GITHUB_ACCESS_PSW}
                        '''

                        // Apply the kustomization to create/update secrets
                        // This uses the kustomization.yml file in the 'infrastructure' directory
                        sh 'kubectl apply -k .'

                        // Clean up the temporary secret files
                        sh 'rm db-secret.env git-secret.env'
                    }
                }

                script {
                    dir('infrastructure/helm') {
                        sh 'helm repo add apache-airflow https://airflow.apache.org'
                        sh 'helm repo update'
                        

                        // Deploy Airflow using Helm with the airflow-values.yml configuration
                        // Using 'upgrade --install' ensures idempotency
                        sh 'helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace -f airflow-values.yml'
                        
                    }
                }
            }
        }
        stage('Build Evidently docker Image') {
            agent {
                docker {
                    image 'docker:latest'
                    args '-u root --entrypoint= -v /var/run/docker.sock:/var/run/docker.sock'
                }
            }
          
            steps {
                script {
                   
                    sh 'echo "Building Evidently Docker image with Dockerfile (requires Docker daemon)"'
                    dir('infrastructure/evidently/docker') {
                        // Build the Docker image using the Dockerfile in the specified directory
                        sh 'docker build -t evidently-worker:latest .'
                        // sh 'docker tag evidently-worker:${BUILD_ID} evidently-worker:latest'
                    }
                    
                }

            }
        }
        stage('Deploy Evidently Worker') {
            agent {
                docker { 
                    image 'dtzar/helm-kubectl:3.12.0' // Use an image with both Helm and Kubectl
                    //mount docker socket to allow Helm to use the host's Docker daemon for building images (if needed in the future)
                    args '-u root --entrypoint= -v ${KUBECONFIG}:${KUBECONFIG}:ro'  // Run as root to allow Helm to use entrypoint for commands
                }
            }
            steps {
                script {
                    dir('infrastructure/evidently') {
 
                        sh """
                        helm upgrade --install evidently-worker ./evidently-app --namespace evidently --create-namespace \
                            --set resources.requests.memory=2Gi
                        """
                    }
                }
            }
        }
        
    }
}
