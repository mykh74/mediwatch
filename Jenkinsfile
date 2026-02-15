pipeline {
    agent any

    environment {
        // Jenkins Credentials Binding
        // 'postgres-app-creds': ID for Username/Password credential (e.g. airflow_user / <password>)
        // 'postgres-admin-pass': ID for Secret Text credential (postgres superuser password)
        POSTGRES_APP = credentials('postgres-app-creds')
        POSTGRES_ADMIN = credentials('postgres-admin-pass')
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
                    dir('orchestration/airflow/helm') {
                        sh 'helm repo add bitnami https://charts.bitnami.com/bitnami'
                        sh 'helm repo update'

                        // Deploy Postgres using Helm, injecting secrets from Jenkins credentials
                        // Using 'upgrade --install' ensures idempotency
                        sh """
                            helm upgrade --install postgres bitnami/postgresql \
                                -f orchestration/airflow/helm/postgres-values.yml \
                                --set auth.username=${POSTGRES_APP_USR} \
                                --set auth.password=${POSTGRES_APP_PSW} \
                                --set auth.postgresPassword=${POSTGRES_ADMIN} \
                                --wait
                        """
                    }
                }
            }
        }
    }
}
