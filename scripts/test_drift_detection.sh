#!/bin/bash
# Test Evidently Drift Detection Implementation

set -e

echo "=========================================="
echo "🧪 Testing Evidently Drift Detection"
echo "=========================================="

# Set environment variables
export REFERENCE_DATA_PATH="./data/processed/train.csv"
export CURRENT_DATA_PATH="./data/processed/test.csv"
export TARGET_COLUMN="readmitted"
export DRIFT_OUTPUT_DIR="./monitoring/reports"
export MLFLOW_TRACKING_URI="http://localhost:5000"

# Create output directory
mkdir -p "${DRIFT_OUTPUT_DIR}"

echo ""
echo "📊 Running drift detection locally..."
echo "  Reference data: ${REFERENCE_DATA_PATH}"
echo "  Current data: ${CURRENT_DATA_PATH}"
echo "  Output: ${DRIFT_OUTPUT_DIR}"

# Run drift detection
python3 scripts/detect_drift.py

echo ""
echo "=========================================="
echo "✅ Drift Detection Test Complete"
echo "=========================================="
echo ""
echo "📄 Check reports in: ${DRIFT_OUTPUT_DIR}"
echo "   - drift_report_latest.html"
echo "   - drift_metrics_latest.json"
echo ""
echo "🔗 View in MLflow: ${MLFLOW_TRACKING_URI}"
echo ""
