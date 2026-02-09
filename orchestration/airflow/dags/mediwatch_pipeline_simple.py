"""
MediWatch ML Pipeline DAG - Simplified Version

Airflow DAG for orchestrating ML pipeline without external dependencies.
Uses direct API calls and shell commands.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Default arguments
default_args = {
    'owner': 'mediwatch',
    'depends_on_past': False,
    'email': ['alerts@mediwatch.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'execution_timeout': timedelta(hours=1),
}

# DAG definition
dag = DAG(
    'mediwatch_ml_pipeline_simple',
    default_args=default_args,
    description='Simplified ML pipeline using API calls',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'healthcare', 'mediwatch', 'simple'],
)


def check_api_health(**context):
    """Check if MediWatch API is healthy."""
    import requests
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        response = requests.get('http://mediwatch-api-service.mediwatch.svc.cluster.local/health', timeout=10)
        response.raise_for_status()
        health_data = response.json()
        
        logger.info(f"API Health: {health_data}")
        
        if health_data.get('model_loaded'):
            logger.info("✓ Model is loaded and ready")
            context['task_instance'].xcom_push(key='api_healthy', value=True)
            return "API health check passed"
        else:
            logger.warning("⚠ Model not loaded in API")
            context['task_instance'].xcom_push(key='api_healthy', value=False)
            return "API healthy but model not loaded"
            
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        raise


def check_mlflow_connection(**context):
    """Verify MLflow connectivity."""
    import requests
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        response = requests.get('http://mlflow-service.mediwatch.svc.cluster.local:5000/health', timeout=10)
        response.raise_for_status()
        
        logger.info("✓ MLflow is accessible")
        context['task_instance'].xcom_push(key='mlflow_healthy', value=True)
        return "MLflow connection successful"
        
    except Exception as e:
        logger.error(f"MLflow connection failed: {e}")
        raise


def test_prediction(**context):
    """Test prediction endpoint with sample data."""
    import requests
    import logging
    import json
    
    logger = logging.getLogger(__name__)
    
    # Sample patient data for testing
    sample_patient = {
        "race": "Caucasian",
        "gender": "Female",
        "age": "[50-60)",
        "admission_type_id": 1,
        "discharge_disposition_id": 1,
        "admission_source_id": 7,
        "time_in_hospital": 3,
        "num_lab_procedures": 50,
        "num_procedures": 0,
        "num_medications": 10,
        "number_outpatient": 0,
        "number_emergency": 0,
        "number_inpatient": 0,
        "diag_1": "250.83",
        "diag_2": "250",
        "diag_3": "V58",
        "number_diagnoses": 9,
        "max_glu_serum": "None",
        "A1Cresult": "None",
        "metformin": "No",
        "repaglinide": "No",
        "nateglinide": "No",
        "chlorpropamide": "No",
        "glimepiride": "No",
        "glipizide": "No",
        "glyburide": "No",
        "pioglitazone": "No",
        "rosiglitazone": "No",
        "acarbose": "No",
        "miglitol": "No",
        "insulin": "Up",
        "glyburide_metformin": "No",
        "change": "Ch",
        "diabetesMed": "Yes"
    }
    
    try:
        response = requests.post(
            'http://mediwatch-api-service.mediwatch.svc.cluster.local/predict',
            json=sample_patient,
            timeout=30
        )
        response.raise_for_status()
        prediction = response.json()
        
        logger.info(f"✓ Prediction successful: {json.dumps(prediction, indent=2)}")
        
        context['task_instance'].xcom_push(key='prediction_result', value=prediction)
        context['task_instance'].xcom_push(key='readmission_probability', value=prediction.get('readmission_probability'))
        
        return f"Prediction: {prediction.get('prediction_label')}, Probability: {prediction.get('readmission_probability'):.2%}"
        
    except Exception as e:
        logger.error(f"Prediction test failed: {e}")
        raise


def validate_system_components(**context):
    """Validate all system components are working."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Get results from previous tasks
    api_healthy = context['task_instance'].xcom_pull(task_ids='check_api_health', key='api_healthy')
    mlflow_healthy = context['task_instance'].xcom_pull(task_ids='check_mlflow_connection', key='mlflow_healthy')
    prediction = context['task_instance'].xcom_pull(task_ids='test_prediction', key='prediction_result')
    
    logger.info("System Validation Summary:")
    logger.info(f"  API Health: {'✓' if api_healthy else '✗'}")
    logger.info(f"  MLflow: {'✓' if mlflow_healthy else '✗'}")
    logger.info(f"  Predictions: {'✓' if prediction else '✗'}")
    
    if api_healthy and mlflow_healthy and prediction:
        logger.info("✓ All system components validated successfully")
        return "System validation passed"
    else:
        logger.error("✗ System validation failed")
        raise Exception("One or more components failed validation")


def generate_pipeline_report(**context):
    """Generate summary report of pipeline execution."""
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    # Collect all metrics from previous tasks
    api_healthy = context['task_instance'].xcom_pull(task_ids='check_api_health', key='api_healthy')
    mlflow_healthy = context['task_instance'].xcom_pull(task_ids='check_mlflow_connection', key='mlflow_healthy')
    prediction = context['task_instance'].xcom_pull(task_ids='test_prediction', key='prediction_result')
    prob = context['task_instance'].xcom_pull(task_ids='test_prediction', key='readmission_probability')
    
    report = f"""
    ========================================
    MediWatch Pipeline Execution Report
    ========================================
    Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    DAG Run ID: {context['dag_run'].run_id}
    
    Component Status:
    - API Health: {'✓ Healthy' if api_healthy else '✗ Unhealthy'}
    - MLflow: {'✓ Connected' if mlflow_healthy else '✗ Disconnected'}
    - Prediction Service: {'✓ Working' if prediction else '✗ Failed'}
    
    Test Prediction Results:
    - Prediction: {prediction.get('prediction_label') if prediction else 'N/A'}
    - Probability: {f'{prob:.2%}' if prob else 'N/A'}
    - Risk Level: {prediction.get('risk_level') if prediction else 'N/A'}
    
    Pipeline Status: SUCCESS
    ========================================
    """
    
    logger.info(report)
    
    # Store report for archiving
    context['task_instance'].xcom_push(key='pipeline_report', value=report)
    
    return "Report generated successfully"


# Create tasks
check_api_task = PythonOperator(
    task_id='check_api_health',
    python_callable=check_api_health,
    dag=dag
)

check_mlflow_task = PythonOperator(
    task_id='check_mlflow_connection',
    python_callable=check_mlflow_connection,
    dag=dag
)

test_prediction_task = PythonOperator(
    task_id='test_prediction',
    python_callable=test_prediction,
    dag=dag
)

validate_task = PythonOperator(
    task_id='validate_system_components',
    python_callable=validate_system_components,
    dag=dag
)

report_task = PythonOperator(
    task_id='generate_pipeline_report',
    python_callable=generate_pipeline_report,
    dag=dag
)

notification_task = BashOperator(
    task_id='send_notification',
    bash_command='echo "✓ MediWatch ML Pipeline completed successfully at $(date)"',
    dag=dag
)

# Define dependencies
[check_api_task, check_mlflow_task] >> test_prediction_task >> validate_task >> report_task >> notification_task
