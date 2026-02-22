import sys
import json
import pandas as pd
import mlflow
from evidently import Report
from evidently.metrics import *
from evidently.presets import *

def run_monitoring(ref_path, cur_path):
    # Load data
    ref = pd.read_csv(ref_path)
    cur = pd.read_csv(cur_path)
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)
    
    # Log to MLflow
    with mlflow.start_run(run_name="Drift_Detection"):
        metrics = report.as_dict()
        drift_score = metrics['metrics'][0]['result']['share_of_drifted_columns']
        mlflow.log_metric("drift_share", drift_score)
        
        # Write to Airflow XCom location
        with open('/airflow/xcom/return.json', 'w') as f:
            json.dump({"drift_detected": drift_score > 0.5}, f)

if __name__ == "__main__":
    print("Starting drift detection...")
    run_monitoring(sys.argv[1], sys.argv[2])