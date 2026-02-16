pipeline {
    agent {
        docker { 
            image 'alpine/helm:3.12.0' // Use a specific version for stability

            args '-u root --entrypoint=' // Run as root to allow Helm to use entrypoint for commands
        }
    }

    environment {
        // Jenkins Credentials Binding
        // 'postgres-app-creds': ID for Username/Password credential (e.g. airflow_user / <password>)
        // 'postgres-admin-pass': ID for Secret Text credential (postgres superuser password)
        POSTGRES_APP = credentials('postgres-user-account')
        POSTGRES_ADMIN = credentials('postgres-admin-password')
        KUBECONFIG = credentials('local-kube-config') // File credential for kubeconfig
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Deploy Postgres') {
            steps {

                withCredentials([file(credentialsId: 'local-kube-config', variable: 'KUBECONFIG_PATH')]) {
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
                                    --wait
                            '''
                        }
                    }
                }
            }
        }
    }
}
