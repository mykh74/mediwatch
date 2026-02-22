import sys
import json
import mlflow
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

def run_monitoring(ref_path, cur_path):
    # Load data (simplified for example)
    # ref = pd.read_csv(ref_path) ...
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref_path, current_data=cur_path)
    
    # Log to MLflow
    with mlflow.start_run(run_name="Drift_Detection"):
        metrics = report.as_dict()
        drift_score = metrics['metrics'][0]['result']['share_of_drifting_columns']
        mlflow.log_metric("drift_share", drift_score)
        
        # Write to Airflow XCom location
        with open('/airflow/xcom/return.json', 'w') as f:
            json.dump({"drift_detected": drift_score > 0.5}, f)

if __name__ == "__main__":
    print("Starting drift detection...")
    run_monitoring(sys.argv[1], sys.argv[2])