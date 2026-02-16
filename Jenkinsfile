pipeline {
    agent {
        docker { 
            image 'dtzar/helm-kubectl:3.12.0' // Use an image with both Helm and Kubectl

            args '-u root --entrypoint=' // Run as root to allow Helm to use entrypoint for commands
        }
    }

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
            steps {
                checkout scm
            }
        }
        
        stage('Deploy Postgres') {
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
            steps {

                script{
                    // Construct the SQLAlchemy connection string
                    // Format: postgresql://user:password@host:port/database
                    // Note: If your password has special characters, it must be URL-encoded.
                    def dbConnection = "postgresql://${POSTGRES_APP_USR}:${POSTGRES_APP_PSW}@${DB_HOST}:5432/${DB_NAME}"
                    
                    // Ensure the namespace exists before creating secrets in it
                    sh 'kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -'

                    // 3. Create the Kubernetes Secret
                    // The 'airflow-values.yml' points to 'airflow-db-secret'.
                    // The official Airflow chart expects the key 'connection' inside this secret.
                    sh """
                        kubectl create secret generic airflow-db-secret \
                        --from-literal=connection="${dbConnection}" \
                        -n airflow \
                        --dry-run=client -o yaml | kubectl apply -f -
                    """


                    // Create a Kubernetes secret for Airflow to access Git using the Jenkins credentials
                    sh '''
                        kubectl create secret generic airflow-git-credentials \
                            --from-literal=GIT_SYNC_USERNAME=${GITHUB_ACCESS_USR} \
                            --from-literal=GIT_SYNC_PASSWORD=${GITHUB_ACCESS_PSW} \
                            --from-literal=GITSYNC_USERNAME=${GITHUB_ACCESS_USR} \
                            --from-literal=GITSYNC_PASSWORD=${GITHUB_ACCESS_PSW} \
                            -n airflow \
                            --dry-run=client -o yaml | kubectl apply -f -
                    '''
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
    }
}
