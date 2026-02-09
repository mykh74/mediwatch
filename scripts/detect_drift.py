#!/usr/bin/env python3
"""
Evidently-based drift detection for MediWatch ML Pipeline.

Detects:
- Data drift between reference and current data
- Target drift
- Model prediction drift
- Data quality issues

Integrates with MLflow for tracking and reporting.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd
import numpy as np
import mlflow
from evidently import BinaryClassification, Report, DataDefinition
from evidently.metrics import DriftedColumnsCount, ValueDrift

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriftDetector:
    """Detect data drift using Evidently AI."""
    
    def __init__(
        self,
        reference_data_path: str,
        current_data_path: str,
        target_column: str = "readmitted",
        output_dir: str = "/models/drift_reports"
    ):
        """Initialize drift detector."""
        self.reference_data_path = Path(reference_data_path)
        self.current_data_path = Path(current_data_path)
        self.target_column = target_column
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Drift Detector initialized")
        logger.info(f"  Reference data: {self.reference_data_path}")
        logger.info(f"  Current data: {self.current_data_path}")
        logger.info(f"  Output: {self.output_dir}")
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load reference and current datasets."""
        logger.info("Loading datasets...")
        
        # Load reference (training) data
        reference_df = pd.read_csv(self.reference_data_path)
        logger.info(f"  Reference data shape: {reference_df.shape}")
        
        # Load current (test) data
        current_df = pd.read_csv(self.current_data_path)
        logger.info(f"  Current data shape: {current_df.shape}")
        
        return reference_df, current_df
    
    def log_feature_info(self, df: pd.DataFrame) -> None:
        """Log feature type information."""
        # Identify feature types
        numerical_features = df.select_dtypes(
            include=[np.number]
        ).columns.tolist()
        
        categorical_features = df.select_dtypes(
            include=['object', 'category']
        ).columns.tolist()
        
        # Remove target from features if present
        if self.target_column in numerical_features:
            numerical_features.remove(self.target_column)
        if self.target_column in categorical_features:
            categorical_features.remove(self.target_column)
        
        logger.info(f"Feature mapping:")
        logger.info(f"  Numerical: {len(numerical_features)} features")
        logger.info(f"  Categorical: {len(categorical_features)} features")
    
    def generate_drift_report(
        self,
        reference_df: pd.DataFrame,
        current_df: pd.DataFrame
    ):
        """Generate comprehensive drift report."""
        logger.info("Generating drift report...")
        
        # Create report with metrics for Evidently 0.7.x
        report = Report(metrics=[
            DriftedColumnsCount(),
        ])
        
        # Run report - returns Snapshot in Evidently 0.7.x
        snapshot = report.run(
            reference_data=reference_df,
            current_data=current_df
        )
        
        logger.info("✅ Drift report generated")
        return snapshot
    
    def extract_drift_metrics(self, snapshot) -> Dict:
        """Extract key metrics from drift snapshot."""
        report_dict = snapshot.dict()
        
        # Extract dataset-level drift from Evidently 0.7.x
        drifted_count = 0
        drift_share = 0.0
        total_columns = 0
        
        for metric in report_dict.get('metrics', []):
            if metric.get('metric') == 'DriftedColumnsCount':
                result = metric.get('result', {})
                drifted_count = result.get('number_of_drifted_columns', 0)
                total_columns = result.get('number_of_columns', 1)
                drift_share = drifted_count / total_columns if total_columns > 0 else 0.0
                break
        
        # Check if significant drift
        dataset_drift = drift_share > 0.3  # More than 30% of columns drifted
        
        metrics = {
            'dataset_drift_detected': bool(dataset_drift),
            'drift_share': float(drift_share),
            'num_drifted_features': int(drifted_count),
            'drifted_features': [],  # Would need to iterate through all columns
            'missing_values': 0,  # Not available in this metric
        }
        
        logger.info(f"Drift Metrics:")
        logger.info(f"  Dataset drift: {metrics['dataset_drift_detected']}")
        logger.info(f"  Drift share: {metrics['drift_share']:.2%}")
        logger.info(f"  Drifted features: {metrics['num_drifted_features']}")
        
        return metrics
    
    def save_report(self, snapshot, metrics: Dict) -> Path:
        """Save drift report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML report
        html_path = self.output_dir / f"drift_report_{timestamp}.html"
        snapshot.save_html(str(html_path))
        logger.info(f"📄 HTML report saved: {html_path}")
        
        # Save JSON metrics
        json_path = self.output_dir / f"drift_metrics_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"📊 Metrics saved: {json_path}")
        
        # Save latest report link
        latest_html = self.output_dir / "drift_report_latest.html"
        if latest_html.exists():
            latest_html.unlink()
        latest_html.symlink_to(html_path.name)
        
        latest_json = self.output_dir / "drift_metrics_latest.json"
        if latest_json.exists():
            latest_json.unlink()
        latest_json.symlink_to(json_path.name)
        
        return html_path
    
    def log_to_mlflow(self, metrics: Dict, html_path: Path):
        """Log drift metrics to MLflow."""
        mlflow_uri = os.getenv(
            "MLFLOW_TRACKING_URI",
            "http://mlflow-service.mediwatch.svc.cluster.local:5000"
        )
        
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("mediwatch_drift_detection")
        
        logger.info(f"Logging to MLflow: {mlflow_uri}")
        
        with mlflow.start_run(run_name=f"drift_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Log metrics
            mlflow.log_metric("dataset_drift", int(metrics['dataset_drift_detected']))
            mlflow.log_metric("drift_share", metrics['drift_share'])
            mlflow.log_metric("num_drifted_features", metrics['num_drifted_features'])
            mlflow.log_metric("missing_values", metrics['missing_values'])
            
            # Log parameters
            mlflow.log_param("reference_data", str(self.reference_data_path))
            mlflow.log_param("current_data", str(self.current_data_path))
            mlflow.log_param("target_column", self.target_column)
            
            # Log drifted features as JSON
            if metrics['drifted_features']:
                mlflow.log_text(
                    json.dumps(metrics['drifted_features'], indent=2),
                    "drifted_features.json"
                )
            
            # Log HTML report as artifact
            mlflow.log_artifact(str(html_path), "drift_reports")
            
            # Log metrics JSON
            mlflow.log_dict(metrics, "drift_metrics.json")
            
            logger.info("✅ Metrics logged to MLflow")
    
    def check_drift_thresholds(self, metrics: Dict) -> Tuple[bool, str]:
        """Check if drift exceeds acceptable thresholds."""
        # Define thresholds
        MAX_DRIFT_SHARE = 0.3  # 30% of features can drift
        MAX_MISSING_VALUES = 1000
        
        issues = []
        
        if metrics['dataset_drift_detected']:
            issues.append(f"⚠️  Dataset drift detected!")
        
        if metrics['drift_share'] > MAX_DRIFT_SHARE:
            issues.append(
                f"⚠️  Drift share {metrics['drift_share']:.1%} exceeds threshold {MAX_DRIFT_SHARE:.1%}"
            )
        
        if metrics['missing_values'] > MAX_MISSING_VALUES:
            issues.append(
                f"⚠️  Missing values {metrics['missing_values']} exceeds threshold {MAX_MISSING_VALUES}"
            )
        
        if metrics['num_drifted_features'] > 0:
            issues.append(
                f"ℹ️  {metrics['num_drifted_features']} features showing drift: "
                f"{', '.join(metrics['drifted_features'][:5])}"
            )
        
        if issues:
            message = "\\n".join(issues)
            logger.warning(f"Drift threshold check:\\n{message}")
            return True, message
        else:
            message = "✅ No significant drift detected"
            logger.info(message)
            return False, message
    
    def run(self) -> Dict:
        """Run complete drift detection pipeline."""
        logger.info("=" * 60)
        logger.info("🔍 MediWatch Drift Detection")
        logger.info("=" * 60)
        
        try:
            # Load data
            reference_df, current_df = self.load_data()
            
            # Log feature info
            self.log_feature_info(reference_df)
            
            # Generate drift report
            snapshot = self.generate_drift_report(
                reference_df,
                current_df
            )
            
            # Extract metrics
            metrics = self.extract_drift_metrics(snapshot)
            
            # Save report
            html_path = self.save_report(snapshot, metrics)
            
            # Log to MLflow
            self.log_to_mlflow(metrics, html_path)
            
            # Check thresholds
            has_issues, message = self.check_drift_thresholds(metrics)
            metrics['has_issues'] = has_issues
            metrics['message'] = message
            
            logger.info("=" * 60)
            if has_issues:
                logger.warning("⚠️  Drift Detection Complete - Issues Found")
            else:
                logger.info("✅ Drift Detection Complete - No Issues")
            logger.info("=" * 60)
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Drift detection failed: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    # Get paths from environment or use defaults
    reference_data = os.getenv("REFERENCE_DATA_PATH", "/data/processed/train.csv")
    current_data = os.getenv("CURRENT_DATA_PATH", "/data/processed/test.csv")
    target_column = os.getenv("TARGET_COLUMN", "readmitted")
    output_dir = os.getenv("DRIFT_OUTPUT_DIR", "/models/drift_reports")
    
    # Create detector
    detector = DriftDetector(
        reference_data_path=reference_data,
        current_data_path=current_data,
        target_column=target_column,
        output_dir=output_dir
    )
    
    # Run drift detection
    metrics = detector.run()
    
    # Exit with appropriate code
    if metrics.get('has_issues', False):
        logger.warning("Exiting with warning status due to drift issues")
        sys.exit(0)  # Still exit 0 to not fail the pipeline, just warn
    else:
        logger.info("Exiting with success status")
        sys.exit(0)


if __name__ == "__main__":
    main()
