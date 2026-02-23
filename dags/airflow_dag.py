from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

from datetime import datetime

with DAG("evidently_drift_check", start_date=datetime(2024, 1, 1), schedule=None) as dag:
    print("DAG started")
    check_drift = KubernetesPodOperator(
        task_id="run_evidently_drift_check",
        name="evidently-drift-pod",
        namespace="airflow-kpo",
        service_account_name="kpo-executor",
        image="evidently-worker:latest",
        # Pass data paths as arguments
        arguments=["my_arg0", "my_arg1"],  
        # Enable XCom to pass the 'drift_detected' flag back to Airflow
        do_xcom_push=True,
        # Ensure the pod cleans up after running
        is_delete_operator_pod=True,
        # Environment variables for MLflow or AWS
        env_vars={"MLFLOW_TRACKING_URI": "http://mlflow:5432"}
    )