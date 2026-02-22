pipeline {
    agent any

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
        stage('Build Docker Images'){
            stages{
                stage('Build Airflow Docker Image'){
                    steps{
                        script{
                            dir('infrastructure/helm') {
                               def airflowImage = docker.build("airflow-custom:latest", "./airflow")

                            //    airflowImage.tag("airflow-custom:${env.BUILD_ID}")
                            //    airflowImage.tag("airflow-custom:latest")
                               //airflowImage.push("airflow-custom:${env.BUILD_ID}")
                               // airflowImage.push()
                                //Push to docker registry
                                docker.withRegistry('localhost', '') {
                                    airflowImage.push("latest")
                                }
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
                        
                            dir('infrastructure/evidently/docker') {
                                // Build the Docker image using the Dockerfile in the specified directory
                                sh label: 'Building Evidently Docker image', script: '''
                                    docker build -t evidently-worker:latest .
                                '''
                                // sh 'docker tag evidently-worker:${BUILD_ID} evidently-worker:latest'
                            }
                        }
                    }
                }
            }
        }
        
        
        stage('Deploy') {
            agent {
                docker { 
                    image 'dtzar/helm-kubectl:3.12.0'
                    args '-u root --entrypoint= -v ${KUBECONFIG}:${KUBECONFIG}:ro'
                }
            }
            stages{
                stage('Deploy to Postgress') {
                    //echo 'Deploying Postgres (named step)'
                    steps{

                        dir('infrastructure/helm') {
                            sh 'helm repo add bitnami https://charts.bitnami.com/bitnami || true'
                            sh 'helm repo update'
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
                stage('Deploy Airflow'){
                    steps{
                        script{// Confirm Github token provides access to the repository
                            sh label: 'Checking GitHub access with provided token', script: '''
                                curl -H "Authorization: token ${GITHUB_ACCESS_PSW}" \
                                -H "Accept: application/vnd.github.v3+json" \
                                https://api.github.com/repos/mykh74/mediwatch \
                                | jq 'has("status") | not' || true
                            '''
                            dir('infrastructure') {
                                // Create namespace and secrets for Airflow, then apply kustomization file
                                sh 'kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -'
                                def dbConnection = 'postgresql://${POSTGRES_APP_USR}:${POSTGRES_APP_PSW}@${DB_HOST}:5432/${DB_NAME}'
                                writeFile file: 'db-secret.env', text: 'connection=${dbConnection}'
                                writeFile file: 'git-secret.env', text: '''
                                    GIT_SYNC_USERNAME=${GITHUB_ACCESS_USR}
                                    GIT_SYNC_PASSWORD=${GITHUB_ACCESS_PSW}
                                    GITSYNC_USERNAME=${GITHUB_ACCESS_USR}
                                    GITSYNC_PASSWORD=${GITHUB_ACCESS_PSW}
                                '''
                                sh 'kubectl apply -k .'
                                sh 'rm db-secret.env git-secret.env'
                            }
                            //echo 'Deploying airflow with Helm (named step)'
                            dir('infrastructure/helm') {
                                sh label: 'Deploying Airflow with Helm', script: '''
                                    helm repo add apache-airflow https://airflow.apache.org || true
                                    helm repo update
                                    helm upgrade --install airflow apache-airflow/airflow \
                                        --namespace airflow \
                                        --create-namespace \
                                        -f airflow-values.yml
                                '''
                               
                            }
                        }

                    }
                }
                stage("Deploy MLflow"){
                    steps{
                        // Named step: MLflow
                        //echo 'Deploying MLflow (named step)'
                        dir('infrastructure/helm') {
                            sh label: 'Deploying MLflow with Helm', script: '''
                                helm repo add community-charts https://community-charts.github.io || true
                                helm repo update
                                helm upgrade --install mlflow community-charts/mlflow \
                                    --namespace mlflow \
                                    --create-namespace \
                                    -f mlflow-values.yml || true
                            '''
                            // sh 'helm repo add community-charts https://community-charts.github.io || true'
                            // sh 'helm repo update'
                            // sh 'helm upgrade --install mlflow community-charts/mlflow --namespace mlflow --create-namespace -f mlflow-values.yml || true'
                        }
                    }
                }
                // stage("Deploy Evidently") {
                //     steps {
                //         dir('infrastructure/helm') {
                //             sh label: 'Deploying Evidently with Helm', script: '''
                //             helm upgrade --install evidently-worker ./evidently-app --namespace evidently --create-namespace \
                //                 --set resources.requests.memory=2Gi
                //             '''
                //         }
                //     }
                // }
            }
        }
        
    }
}
