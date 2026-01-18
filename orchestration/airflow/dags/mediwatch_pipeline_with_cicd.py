"""
Airflow DAG with Jenkins CI/CD Integration

This enhanced DAG includes Jenkins deployment automation:
1. Data preprocessing
2. Model training
3. Model evaluation
4. Drift detection
5. **Jenkins build trigger** (NEW)
6. **Deployment automation** (NEW)
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the Jenkins trigger
from ci_cd.scripts.trigger_jenkins import trigger_jenkins_build

# Default arguments
default_args = {
    'owner': 'mediwatch',
    'depends_on_past': False,
    'email': ['alerts@mediwatch.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# DAG definition
dag = DAG(
    'mediwatch_ml_pipeline_with_cicd',
    default_args=default_args,
    description='Complete ML pipeline with Jenkins CI/CD integration',
    schedule_interval='@weekly',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['ml', 'healthcare', 'mediwatch', 'ci-cd'],
)


def trigger_deployment(**context):
    """
    Trigger Jenkins deployment after successful model training.
    
    This function:
    1. Checks if model training was successful
    2. Triggers Jenkins build
    3. Monitors build status
    4. Returns deployment status
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Get metrics from previous task
    ti = context['ti']
    metrics = ti.xcom_pull(task_ids='evaluate_best_model')
    
    if not metrics:
        logger.warning("No metrics found from training. Skipping deployment.")
        return False
    
    f1_score = metrics.get('f1', 0)
    
    # Only deploy if model meets quality threshold
    if f1_score < 0.50:
        logger.warning(f"Model F1 score ({f1_score:.3f}) below threshold (0.50). Skipping deployment.")
        return False
    
    logger.info(f"Model F1 score ({f1_score:.3f}) meets threshold. Triggering deployment...")
    
    # Trigger Jenkins build
    try:
        build_number = trigger_jenkins_build(
            jenkins_url="http://localhost:8080",
            job_name="mediwatch-ci-cd",
            token="mediwatch-build-token",
            parameters={
                "DEPLOY_MODE": "docker",
                "RUN_TESTS": True,
                "CUSTOM_TAG": f"airflow-{context['ds_nodash']}"
            },
            wait=True,
            timeout=300
        )
        
        if build_number:
            logger.info(f"✓ Jenkins build #{build_number} triggered successfully!")
            ti.xcom_push(key='jenkins_build_number', value=build_number)
            return True
        else:
            logger.error("✗ Failed to trigger Jenkins build")
            return False
            
    except Exception as e:
        logger.error(f"Error triggering Jenkins: {e}")
        return False


def monitor_deployment(**context):
    """
    Monitor Jenkins build progress.
    
    This is a separate task to monitor deployment completion.
    """
    import logging
    import time
    from ci_cd.scripts.trigger_jenkins import JenkinsTrigger
    
    logger = logging.getLogger(__name__)
    ti = context['ti']
    
    # Get build number from previous task
    build_number = ti.xcom_pull(task_ids='trigger_jenkins_deployment', key='jenkins_build_number')
    
    if not build_number:
        logger.warning("No build number found. Skipping monitoring.")
        return False
    
    logger.info(f"Monitoring Jenkins build #{build_number}...")
    
    # Create Jenkins client
    client = JenkinsTrigger(jenkins_url="http://localhost:8080")
    
    # Wait for completion
    success = client.wait_for_completion(
        job_name="mediwatch-ci-cd",
        build_number=build_number,
        timeout=600,
        poll_interval=10
    )
    
    if success:
        logger.info("✓ Deployment completed successfully!")
        return True
    else:
        logger.error("✗ Deployment failed!")
        raise Exception("Jenkins deployment failed")


# Task definitions (using existing tasks from mediwatch_pipeline.py)

# ... (include existing tasks: download_data, preprocess, train_baseline, etc.)

# NEW: Jenkins deployment tasks

trigger_jenkins = PythonOperator(
    task_id='trigger_jenkins_deployment',
    python_callable=trigger_deployment,
    provide_context=True,
    dag=dag,
)

monitor_jenkins = PythonOperator(
    task_id='monitor_jenkins_deployment',
    python_callable=monitor_deployment,
    provide_context=True,
    dag=dag,
)

# Task dependencies with CI/CD integration
# evaluate_best_model >> trigger_jenkins >> monitor_jenkins

# Alternative: Use SimpleHttpOperator for simpler triggering
# (if apache-airflow-providers-http is installed)

"""
from airflow.providers.http.operators.http import SimpleHttpOperator

trigger_jenkins_http = SimpleHttpOperator(
    task_id='trigger_jenkins_http',
    http_conn_id='jenkins_default',  # Configure in Airflow Connections
    endpoint='/job/mediwatch-ci-cd/buildWithParameters',
    method='POST',
    data={
        'token': 'mediwatch-build-token',
        'DEPLOY_MODE': 'docker',
        'RUN_TESTS': 'true'
    },
    response_check=lambda response: response.status_code == 201,
    dag=dag
)
"""
