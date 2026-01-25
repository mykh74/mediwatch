from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def print_hello():
    """Function to be executed by the PythonOperator"""
    print("Hello World! The DAG is working.")
    return "Hello World"

with DAG(
    dag_id='hello_world_test',
    default_args=default_args,
    description='A simple Hello World DAG for testing configuration',
    start_date=datetime(2024, 1, 1),
    schedule=None,  # Manual trigger only
    catchup=False,
    tags=['test', 'example'],
) as dag:

    task_hello = PythonOperator(
        task_id='print_hello_task',
        python_callable=print_hello,
    )