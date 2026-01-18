import pandas as pd
from evidently import Report
from evidently.metrics import *
from evidently.presets import *

def detect_drift(reference_path, current_path, output_file="drift_report.html"):
    # 1. Load the datasets
    try:
        reference_data = pd.read_csv(reference_path)
        current_data = pd.read_csv(current_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # 2. Create the Data Drift Report
    # The DataDriftPreset automatically selects the best statistical tests 
    # based on your data types (e.g., Jensen-Shannon for categorical, 
    # population stability index for numerical).
    report = Report(metrics=[
        DataDriftPreset(),
    ])

    print("Analyzing data drift... this may take a moment.")
    result = report.run(reference_data=reference_data, current_data=current_data)

    # 3. Save the report to an HTML file
    result.save_html(output_file)
    print(f"Report generated successfully: {output_file}")

if __name__ == "__main__":
    # Update these paths to your actual CSV filenames
    REF_CSV = "data/processed/train.csv"
    CUR_CSV = "data/processed/test.csv"
    
    detect_drift(REF_CSV, CUR_CSV)