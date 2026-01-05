"""
Evidently-based monitoring for data drift and model performance.

This module generates monitoring reports for:
- Data drift detection
- Model performance monitoring
- Prediction drift
- Target drift
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

import pandas as pd
import numpy as np
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset, TargetDriftPreset
from evidently.metrics import (
    DatasetDriftMetric,
    DatasetMissingValuesMetric,
    ClassificationQualityMetric,
    ClassificationClassBalance,
    ClassificationConfusionMatrix,
)

logger = logging.getLogger(__name__)


class MediWatchMonitor:
    """Monitor for MediWatch readmission prediction system."""
    
    def __init__(
        self,
        reference_data: pd.DataFrame,
        target_column: str = "readmitted",
        prediction_column: Optional[str] = "prediction",
        output_dir: Path = Path("monitoring/reports")
    ):
        """Initialize monitor."""
        self.reference_data = reference_data
        self.target_column = target_column
        self.prediction_column = prediction_column
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup column mapping
        self.column_mapping = ColumnMapping(
            target=target_column,
            prediction=prediction_column,
            numerical_features=self._get_numerical_features(),
            categorical_features=self._get_categorical_features()
        )
        
        logger.info(f"Monitor initialized: {reference_data.shape}")
    
    def _get_numerical_features(self) -> List[str]:
        """Get numerical feature names."""
        numerical_cols = self.reference_data.select_dtypes(
            include=[np.number]
        ).columns.tolist()
        
        return [
            col for col in numerical_cols
            if col not in [self.target_column, self.prediction_column]
        ]
    
    def _get_categorical_features(self) -> List[str]:
        """Get categorical feature names."""
        categorical_cols = self.reference_data.select_dtypes(
            include=['object', 'category']
        ).columns.tolist()
        
        return [
            col for col in categorical_cols
            if col not in [self.target_column, self.prediction_column]
        ]
    
    def generate_data_drift_report(
        self,
        current_data: pd.DataFrame,
        report_name: Optional[str] = None
    ) -> Path:
        """Generate data drift report."""
        logger.info("Generating data drift report...")
        
        report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset(),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"data_drift_{timestamp}.html"
        
        report_path = self.output_dir / report_name
        report.save_html(str(report_path))
        
        logger.info(f"Report saved: {report_path}")
        return report_path
    
    def generate_target_drift_report(
        self,
        current_data: pd.DataFrame,
        report_name: Optional[str] = None
    ) -> Path:
        """Generate target drift report."""
        logger.info("Generating target drift report...")
        
        report = Report(metrics=[
            TargetDriftPreset(),
            ClassificationClassBalance(),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"target_drift_{timestamp}.html"
        
        report_path = self.output_dir / report_name
        report.save_html(str(report_path))
        
        logger.info(f"Report saved: {report_path}")
        return report_path
    
    def generate_model_performance_report(
        self,
        current_data: pd.DataFrame,
        report_name: Optional[str] = None
    ) -> Path:
        """Generate model performance report."""
        logger.info("Generating performance report...")
        
        if self.target_column not in current_data.columns:
            raise ValueError(f"Target column '{self.target_column}' not found")
        if self.prediction_column not in current_data.columns:
            raise ValueError(f"Prediction column '{self.prediction_column}' not found")
        
        report = Report(metrics=[
            ClassificationQualityMetric(),
            ClassificationConfusionMatrix(),
            ClassificationClassBalance(),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"model_performance_{timestamp}.html"
        
        report_path = self.output_dir / report_name
        report.save_html(str(report_path))
        
        logger.info(f"Report saved: {report_path}")
        return report_path
    
    def check_drift(self, current_data: pd.DataFrame) -> Dict:
        """Quick drift check returning metrics."""
        logger.info("Performing drift check...")
        
        report = Report(metrics=[
            DatasetDriftMetric(),
            DatasetMissingValuesMetric(),
        ])
        
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        result = report.as_dict()
        
        return {
            "dataset_drift": result["metrics"][0]["result"]["dataset_drift"],
            "drift_share": result["metrics"][0]["result"]["share_of_drifted_columns"],
            "number_of_drifted_columns": result["metrics"][0]["result"]["number_of_drifted_columns"],
            "missing_values_detected": result["metrics"][1]["result"]["current"]["number_of_missing_values"] > 0,
        }


def main() -> None:
    """Generate monitoring reports."""
    logging.basicConfig(level=logging.INFO)
    
    # Load reference data
    reference_df = pd.read_csv("data/processed/train.csv").sample(n=5000, random_state=42)
    current_df = pd.read_csv("data/processed/test.csv").sample(n=1000, random_state=42)
    
    # Initialize monitor
    monitor = MediWatchMonitor(
        reference_data=reference_df,
        target_column="readmitted",
        output_dir=Path("monitoring/reports")
    )
    
    # Generate reports
    print("\\nGenerating data drift report...")
    drift_report = monitor.generate_data_drift_report(current_df)
    print(f"Report saved: {drift_report}")
    
    print("\\nPerforming drift check...")
    drift_metrics = monitor.check_drift(current_df)
    print(f"Drift detected: {drift_metrics['dataset_drift']}")
    print(f"Drifted columns: {drift_metrics['number_of_drifted_columns']}")


if __name__ == "__main__":
    main()
