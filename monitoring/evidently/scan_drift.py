"""
Batch drift scanning for multiple CSV files.

This script scans a directory of CSV files and checks each one for data drift
against a reference dataset using the MediWatchMonitor.
"""
from __future__ import annotations

import argparse
import logging
import glob
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from evidently import Report
from evidently.presets import DataDriftPreset, DataQualityPreset
from evidently.metrics import DatasetDriftMetric, DatasetMissingValuesMetric
from evidently import ColumnMapping

logger = logging.getLogger(__name__)


def scan_files(
    reference_path: Path,
    input_pattern: str,
    output_dir: Path
) -> None:
    """Scan files matching pattern for drift against reference."""
    
    # Load reference data
    logger.info(f"Loading reference data from {reference_path}")
    try:
        reference_df = pd.read_csv(reference_path)
    except Exception as e:
        logger.error(f"Failed to load reference data: {e}")
        return
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup column mapping
    target_column = "readmitted"
    prediction_column = "prediction"
    
    numerical_features = reference_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = reference_df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    for col in [target_column, prediction_column]:
        if col in numerical_features:
            numerical_features.remove(col)
        if col in categorical_features:
            categorical_features.remove(col)
            
    column_mapping = ColumnMapping(
        target=target_column,
        prediction=prediction_column if prediction_column in reference_df.columns else None,
        numerical_features=numerical_features,
        categorical_features=categorical_features
    )
    
    # Find files
    input_path = Path(input_pattern)
    files: List[Path] = []
    
    if input_path.is_dir():
        files = list(input_path.glob("*.csv"))
    else:
        # Handle glob pattern (e.g., "data/*.csv")
        files = [Path(f) for f in glob.glob(input_pattern) if f.endswith(".csv")]

    if not files:
        logger.warning(f"No CSV files found matching: {input_pattern}")
        return
        
    logger.info(f"Found {len(files)} files to scan.")
    
    results: List[Dict[str, Any]] = []
    
    for file_path in files:
        # Skip reference file if it matches
        if file_path.resolve() == reference_path.resolve():
            continue
            
        logger.info(f"Scanning {file_path.name}...")
        try:
            current_df = pd.read_csv(file_path)
            
            # Check drift
            drift_report = Report(metrics=[
                DatasetDriftMetric(),
                DatasetMissingValuesMetric(),
            ])
            drift_report.run(
                reference_data=reference_df,
                current_data=current_df,
                column_mapping=column_mapping
            )
            drift_result = drift_report.as_dict()
            
            metrics = {
                "dataset_drift": drift_result["metrics"][0]["result"]["dataset_drift"],
                "drift_share": drift_result["metrics"][0]["result"]["share_of_drifted_columns"],
                "number_of_drifted_columns": drift_result["metrics"][0]["result"]["number_of_drifted_columns"],
            }
            
            # Generate report
            report_name = f"drift_report_{file_path.stem}.html"
            full_report = Report(metrics=[
                DataDriftPreset(),
                DataQualityPreset(),
            ])
            full_report.run(
                reference_data=reference_df,
                current_data=current_df,
                column_mapping=column_mapping
            )
            
            report_path = output_dir / report_name
            full_report.save_html(str(report_path))
            logger.info(f"Report saved: {report_path}")
            
            results.append({
                "file": file_path.name,
                "drift_detected": metrics["dataset_drift"],
                "drifted_columns": metrics["number_of_drifted_columns"],
                "share": round(metrics["drift_share"], 3)
            })
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            
    # Print summary
    if results:
        print("\n=== Drift Scan Summary ===")
        summary_df = pd.DataFrame(results)
        print(summary_df.to_string(index=False))
        
        # Save summary
        summary_path = output_dir / "scan_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSummary saved to {summary_path}")
    else:
        print("\nNo files were successfully processed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan multiple CSV files for data drift.")
    parser.add_argument("--reference", required=True, help="Path to reference data CSV")
    parser.add_argument("--input", required=True, help="Input directory or glob pattern for CSV files")
    parser.add_argument("--output", default="monitoring/reports", help="Output directory for reports")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    scan_files(
        Path(args.reference),
        args.input,
        Path(args.output)
    )


if __name__ == "__main__":
    main()
