#!/bin/bash
# Script to trigger the enhanced ML pipeline DAG

echo "🚀 Triggering MediWatch Enhanced ML Pipeline..."

# Get Airflow webserver pod
POD=$(kubectl get pod -n mediwatch -l app=airflow-webserver -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD" ]; then
    echo "❌ Could not find Airflow webserver pod"
    exit 1
fi

echo "📡 Found webserver pod: $POD"

# Trigger the DAG using Python API
kubectl exec -n mediwatch "$POD" -c webserver -- python3 -c "
import sys
sys.path.insert(0, '/opt/airflow')

from airflow.models import DagBag, DagRun
from airflow.utils.state import State
from airflow.utils import timezone
from sqlalchemy import create_engine
from airflow import settings

print('Loading DAGs...')
dagbag = DagBag('/opt/airflow/dags')

dag_id = 'mediwatch_ml_pipeline_enhanced'
if dag_id not in dagbag.dags:
    print(f'❌ DAG {dag_id} not found')
    print(f'Available DAGs: {list(dagbag.dags.keys())}')
    sys.exit(1)

dag = dagbag.dags[dag_id]
print(f'✅ Found DAG: {dag_id}')

# Create dag run
from airflow.utils.session import create_session
from airflow.utils.types import DagRunType

with create_session() as session:
    # Make sure DAG is not paused
    from airflow.models import DagModel
    dag_model = session.query(DagModel).filter(DagModel.dag_id == dag_id).first()
    if dag_model:
        dag_model.is_paused = False
        session.commit()
        print('✅ DAG unpaused')
    
    # Trigger the DAG
    run_id = f'manual__{timezone.utcnow().isoformat()}'
    dag_run = DagRun(
        dag_id=dag_id,
        run_id=run_id,
        run_type=DagRunType.MANUAL,
        state=State.QUEUED,
        execution_date=timezone.utcnow()
    )
    session.add(dag_run)
    session.commit()
    print(f'✅ DAG triggered with run_id: {run_id}')
    print(f'🎯 Monitor at: http://localhost:8080/dags/{dag_id}/grid')
"

echo ""
echo "✅ Pipeline triggered successfully!"
echo "🌐 Monitor progress at: http://localhost:8080"
echo "📊 View run details at: http://localhost:8080/dags/mediwatch_ml_pipeline_enhanced/grid"
