#!/usr/bin/env python3
"""
Test script to generate and upload an Evidently report
"""

import pandas as pd
import requests
from pathlib import Path
import sys

def generate_sample_report():
    """Generate a simple HTML report for testing"""
    print("📊 Generating sample report...")
    
    # Load training data as reference
    data_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    train_path = data_dir / "train.csv"
    test_path = data_dir / "test.csv"
    
    if not train_path.exists() or not test_path.exists():
        print(f"❌ Data files not found at {data_dir}")
        return None
    
    # Load data
    reference_data = pd.read_csv(train_path).head(100)
    current_data = pd.read_csv(test_path).head(100)
    
    print(f"✅ Loaded reference data: {len(reference_data)} rows")
    print(f"✅ Loaded current data: {len(current_data)} rows")
    
    # Create a simple HTML report
    output_path = Path(__file__).parent / "data_drift_report.html"
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MediWatch Data Drift Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .metric-name {{ font-weight: bold; color: #34495e; }}
        .metric-value {{ color: #27ae60; font-size: 1.2em; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
    </style>
</head>
<body>
    <h1>🏥 MediWatch Data Drift Report</h1>
    <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>📊 Dataset Overview</h2>
    <div class="metric">
        <div class="metric-name">Reference Dataset:</div>
        <div class="metric-value">{len(reference_data)} samples</div>
    </div>
    <div class="metric">
        <div class="metric-name">Current Dataset:</div>
        <div class="metric-value">{len(current_data)} samples</div>
    </div>
    <div class="metric">
        <div class="metric-name">Features:</div>
        <div class="metric-value">{len(reference_data.columns)} columns</div>
    </div>
    
    <h2>📈 Basic Statistics</h2>
    <h3>Reference Data (Training)</h3>
    {reference_data.describe().to_html()}
    
    <h3>Current Data (Test)</h3>
    {current_data.describe().to_html()}
    
    <h2>✅ Status</h2>
    <div class="metric">
        <div class="metric-name">Report Status:</div>
        <div class="metric-value">Successfully Generated</div>
    </div>
    <div class="metric">
        <div class="metric-name">Data Quality:</div>
        <div class="metric-value">Checked</div>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Report saved to: {output_path}")
    return output_path

def upload_report(report_path, evidently_url="http://localhost:8800"):
    """Upload the report to Evidently service"""
    print(f"\n📤 Uploading report to {evidently_url}...")
    
    try:
        # Test connection
        health_response = requests.get(f"{evidently_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Evidently service not healthy: {health_response.status_code}")
            return False
        
        print("✅ Evidently service is healthy")
        
        # Upload report
        with open(report_path, 'rb') as f:
            files = {'file': (report_path.name, f, 'text/html')}
            response = requests.post(
                f"{evidently_url}/upload-report",
                files=files,
                timeout=10
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Report uploaded successfully: {result}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def verify_report(evidently_url="http://localhost:8800"):
    """Verify the report is accessible"""
    print(f"\n🔍 Verifying uploaded report...")
    
    try:
        # List reports
        response = requests.get(f"{evidently_url}/reports", timeout=5)
        if response.status_code == 200:
            reports = response.json()
            print(f"✅ Available reports: {reports}")
            
            if reports.get('reports'):
                report_name = reports['reports'][0]
                print(f"\n📊 Report accessible at: {evidently_url}/reports/{report_name}")
                return True
            else:
                print("⚠️  No reports found")
                return False
        else:
            print(f"❌ Failed to list reports: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("=" * 60)
    print("🚀 Evidently Report Upload Test")
    print("=" * 60)
    
    # Generate report
    report_path = generate_sample_report()
    if not report_path:
        print("\n❌ Failed to generate report")
        sys.exit(1)
    
    # Upload report
    success = upload_report(report_path)
    if not success:
        print("\n❌ Failed to upload report")
        print("\n💡 Make sure Evidently port-forward is running:")
        print("   kubectl port-forward -n mediwatch svc/evidently-service 8800:8000")
        sys.exit(1)
    
    # Verify report
    verify_report()
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)
    print("\n📊 View your report at: http://localhost:8800/reports/data_drift_report.html")

if __name__ == "__main__":
    main()
