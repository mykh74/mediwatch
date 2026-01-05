"""
MediWatch ML Pipeline DAG

Airflow DAG for orchestrating the complete ML pipeline:
1. Data extraction and preprocessing
2. Model training and evaluation
3. Model registry and promotion
4. Drift monitoring
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# NOTE: Airflow is not included in requirements.txt by default.
# Install with: pip install apache-airflow


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
    'mediwatch_ml_pipeline',
    default_args=default_args,
    description='Complete ML pipeline for patient readmission prediction',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
    tags=['ml', 'healthcare', 'mediwatch'],
)


def download_data(**context):
    """Download latest patient data."""
    import sys
    sys.path.insert(0, '/app/src')
    from mediwatch.data.load import download_kaggle_dataset, load_diabetes_dataset
    
    download_kaggle_dataset(dataset_name="brandao/diabetes", output_dir="data/raw")
    df = load_diabetes_dataset("data/raw")
    
    context['task_instance'].xcom_push(key='data_rows', value=len(df))
    return "Data download complete"


def preprocess_data(**context):
    """Preprocess data and create train/test splits."""
    import sys
    sys.path.insert(0, '/app/src')
    from mediwatch.data.load import load_diabetes_dataset
    from mediwatch.data.preprocess import preprocess_pipeline
    from pathlib import Path
    
    df = load_diabetes_dataset("data/raw")
    split_data, artifacts = preprocess_pipeline(
        df=df, target_col='readmitted', test_size=0.2,
        artifacts_path=Path('data/processed/preprocessing_artifacts.pkl')
    )
    
    output_dir = Path('data/processed')
    output_dir.mkdir(parents=True, exist_ok=True)
    split_data.train.to_csv(output_dir / 'train.csv', index=False)
    split_data.test.to_csv(output_dir / 'test.csv', index=False)
    
    context['task_instance'].xcom_push(key='train_rows', value=len(split_data.train))
    return "Preprocessing complete"


def train_baseline_models(**context):
    """Train all baseline models."""
    import sys
    sys.path.insert(0, '/app/src')
    import pandas as pd
    from mediwatch.models.train import train_all_baselines
    
    train_df = pd.read_csv('data/processed/train.csv')
    target_col = 'readmitted'
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    results = train_all_baselines(
        x_train=X_train, y_train=y_train, use_scaling=True,
        track_mlflow=True, experiment_name='mediwatch-readmission'
    )
    
    context['task_instance'].xcom_push(key='models_trained', value=len(results))
    return "Baseline training complete"


def evaluate_models(**context):
    """Evaluate all trained models."""
    import sys
    sys.path.insert(0, '/app/src')
    from mediwatch.registry.mlflow_registry import get_best_run
    
    best_run = get_best_run(
        experiment_name='mediwatch-readmission',
        metric='test_f1',
        tracking_uri='http://mlflow:5000'
    )
    
    if best_run:
        best_f1 = best_run.data.metrics.get('test_f1', 0)
        context['task_instance'].xcom_push(key='best_f1', value=best_f1)
        context['task_instance'].xcom_push(key='best_run_id', value=best_run.info.run_id)
    
    return "Evaluation complete"


def hyperparameter_tuning(**context):
    """Run hyperparameter optimization."""
    import sys
    sys.path.insert(0, '/app/src')
    import pandas as pd
    from mediwatch.models.tune import run_hpo
    
    train_df = pd.read_csv('data/processed/train.csv')
    target_col = 'readmitted'
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    hpo_results = run_hpo(
        x_train=X_train, y_train=y_train, model_name="random_forest",
        num_samples=10, max_concurrent_trials=2, cv=3,
        mlflow_experiment_name='mediwatch-readmission'
    )
    
    context['task_instance'].xcom_push(key='hpo_best_score', value=hpo_results['best_score'])
    return "HPO complete"


def register_best_model(**context):
    """Register best model in MLflow registry."""
    import sys
    sys.path.insert(0, '/app/src')
    from mediwatch.registry.mlflow_registry import get_best_run, register_model
    
    best_run = get_best_run(
        experiment_name='mediwatch-readmission',
        metric='test_f1',
        tracking_uri='http://mlflow:5000'
    )
    
    if not best_run:
        raise ValueError("No best run found")
    
    model_uri = f"runs:/{best_run.info.run_id}/model"
    model_version = register_model(
        model_uri=model_uri,
        model_name='mediwatch_readmission_classifier',
        tags={'task': 'readmission_prediction', 'airflow_dag': 'mediwatch_ml_pipeline'},
        description=f"Model registered by Airflow on {datetime.now().strftime('%Y-%m-%d')}"
    )
    
    context['task_instance'].xcom_push(key='model_version', value=model_version.version)
    return "Model registration complete"


def promote_to_production(**context):
    """Promote model to production if threshold met."""
    import sys
    sys.path.insert(0, '/app/src')
    from mediwatch.registry.mlflow_registry import promote_model_to_production
    
    best_f1 = context['task_instance'].xcom_pull(task_ids='evaluate_models', key='best_f1')
    threshold = 0.70
    
    if best_f1 and best_f1 >= threshold:
        promote_model_to_production(
            model_name='mediwatch_readmission_classifier',
            tracking_uri='http://mlflow:5000'
        )
        return "Promotion successful"
    else:
        return "Promotion skipped"


def generate_monitoring_reports(**context):
    """Generate drift and performance monitoring reports."""
    import sys
    sys.path.insert(0, '/app/src')
    import pandas as pd
    from monitoring.evidently.generate_report import MediWatchMonitor
    from pathlib import Path
    
    reference_df = pd.read_csv('data/processed/train.csv').sample(n=5000, random_state=42)
    current_df = pd.read_csv('data/processed/test.csv').sample(n=1000, random_state=42)
    
    monitor = MediWatchMonitor(
        reference_data=reference_df,
        target_column='readmitted',
        output_dir=Path('monitoring/reports')
    )
    
    drift_report = monitor.generate_data_drift_report(current_df)
    drift_metrics = monitor.check_drift(current_df)
    
    context['task_instance'].xcom_push(key='drift_detected', value=drift_metrics['dataset_drift'])
    return "Monitoring reports generated"


# Create tasks
download_task = PythonOperator(task_id='download_data', python_callable=download_data, dag=dag)
preprocess_task = PythonOperator(task_id='preprocess_data', python_callable=preprocess_data, dag=dag)
train_task = PythonOperator(task_id='train_baseline_models', python_callable=train_baseline_models, dag=dag)
evaluate_task = PythonOperator(task_id='evaluate_models', python_callable=evaluate_models, dag=dag)
hpo_task = PythonOperator(task_id='hyperparameter_tuning', python_callable=hyperparameter_tuning, dag=dag)
register_task = PythonOperator(task_id='register_best_model', python_callable=register_best_model, dag=dag)
promote_task = PythonOperator(task_id='promote_to_production', python_callable=promote_to_production, dag=dag)
monitoring_task = PythonOperator(task_id='generate_monitoring_reports', python_callable=generate_monitoring_reports, dag=dag)
notification_task = BashOperator(task_id='send_notification', bash_command='echo "Pipeline completed on $(date)"', dag=dag)

# Define dependencies
download_task >> preprocess_task >> train_task >> evaluate_task >> hpo_task >> register_task >> promote_task >> monitoring_task >> notification_task


def build_dag():
    """Return the DAG for testing."""
    return dag
