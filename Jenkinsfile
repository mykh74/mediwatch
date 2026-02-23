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
            agent {
                docker { 
                    image 'docker:dind' // Use a Docker image with the Docker CLI installed for building and pushing images
                    args '-v /var/run/docker.sock:/var/run/docker.sock' // Mount Docker socket to allow Docker commands to work inside the container, and add host entry for Kubernetes API access
                }
            }
            stages{
                stage('Build Airflow Docker Image'){
                    steps{
                        script{
                            dir('infrastructure/helm') {
                               def airflowImage = docker.build("airflow-custom:latest", "./airflow")
                                //Push to docker registry
                                docker.withRegistry('http://host.docker.internal:5000', '') {
                                    airflowImage.push()
                                    //airflowImage.push("airflow-custom:${env.BUILD_ID}")
                                }
                            }
                        }
                    }
                }

                // stage('Build Evidently docker Image') {
                //     steps{
                //         script{
                //             dir('infrastructure/evidently/docker') {
                //                 def evidentlyImage = docker.build("evidently-worker:latest", "./")
                //                 docker.withRegistry('http://host.docker.internal:5000', '') {
                //                     evidentlyImage.push()
                //                     //evidentlyImage.push("evidently-worker:${env.BUILD_ID}")
                //                 }
                //             }
                //         }
                        
                //     }

                // }
            }
        }
        
        
        stage('Deploy') {
            agent {
                docker { 
                    image 'dtzar/helm-kubectl:3.12.0'
                    //--add-host=kubernetes:host-gateway allows the container to resolve 'kubernetes' to the host's gateway IP, enabling kubectl/helm inside the container to communicate with the Kubernetes API server running on the host machine. 
                    //-v ${KUBECONFIG}:${KUBECONFIG}:ro' mounts the kubeconfig file from the Jenkins host into the container in read-only mode
                    args '--add-host=kubernetes:host-gateway -v ${KUBECONFIG}:${KUBECONFIG}:ro'
                }
            }
            environment{
                // These ensure Helm doesn't try to write to the root (/) directory
                HELM_CACHE_HOME  = "${WORKSPACE}/.helm/cache"
                HELM_CONFIG_HOME = "${WORKSPACE}/.helm/config"
                HELM_DATA_HOME   = "${WORKSPACE}/.helm/data"
            }
            stages{
                stage('Deploy Postgress') {
                    environment{
                       POSTGRES_CHART_URL = 'oci://registry-1.docker.io/bitnamicharts/postgresql' // Using OCI registry URL for Bitnami Postgres Helm chart to avoid issues with helm repo add in some environments
                    }
                    //echo 'Deploying Postgres (named step)'
                    steps{

                        dir('infrastructure/helm') {
                            // sh 'helm repo add bitnami https://charts.bitnami.com/bitnami || true'
                            // sh 'helm repo update'
                            sh '''
                                helm upgrade --install postgres ${POSTGRES_CHART_URL} \
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
                    environment{
                        AIRFLOW_CHART_URL = 'oci://registry-1.docker.io/bitnamicharts/airflow' // Using OCI registry URL for Bitnami Airflow Helm chart to avoid issues with helm repo add in some environments
                    }
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
                            // Apply RBAC for Airflow scheduler to allow it to create pods in airflow-kpo namespace
                            dir('infrastructure/k8s'){
                                sh label: 'Applying Airflow KPO RBAC', script: '''
                                    kubectl apply -f airflow-worker-rbac.yml
                                '''
                            }
                            //echo 'Deploying airflow with Helm (named step)'
                            dir('infrastructure/helm') {
                                sh label: 'Deploying Airflow with Helm', script: '''
                                    helm upgrade --install airflow ${AIRFLOW_CHART_URL} \
                                        --namespace airflow \
                                        --create-namespace \
                                        --set airflowPodAnnotations.git_commit=${gitCommit} \
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
                            // sh label: 'Deploying MLflow with Helm', script: '''
                            //     helm repo add community-charts https://community-charts.github.io || true
                            //     helm repo update
                            //     helm upgrade --install mlflow community-charts/mlflow \
                            //         --namespace mlflow \
                            //         --create-namespace \
                            //         -f mlflow-values.yml || true
                            // '''
                            // sh 'helm repo add community-charts https://community-charts.github.io || true'
                            // sh 'helm repo update'
                            // sh 'helm upgrade --install mlflow community-charts/mlflow --namespace mlflow --create-namespace -f mlflow-values.yml || true'
                        }
                    }
                }
            }
        }
        
    }
}
