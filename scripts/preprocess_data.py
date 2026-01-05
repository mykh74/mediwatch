#!/usr/bin/env python3
"""
Script to run the preprocessing pipeline on the diabetes dataset.

Usage:
    python scripts/preprocess_data.py
    python scripts/preprocess_data.py --input data/raw/diabetic_data.csv --output data/processed
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mediwatch.data.load import load_diabetes_dataset
from mediwatch.data.preprocess import preprocess_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess the diabetes dataset for model training"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw",
        help="Path to input data file or directory (default: data/raw)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
        help="Output directory for processed data (default: data/processed)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="readmitted",
        help="Name of target column (default: readmitted)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of data for test set (default: 0.2)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    try:
        print("=" * 80)
        print("MediWatch Data Preprocessing Pipeline")
        print("=" * 80)

        # Load dataset
        print(f"\nLoading dataset from: {args.input}")
        if Path(args.input).is_file():
            import pandas as pd

            df = pd.read_csv(args.input)
        else:
            df = load_diabetes_dataset(data_dir=args.input)

        print(f"✓ Dataset loaded: {df.shape}")

        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run preprocessing pipeline
        artifacts_path = output_dir / "preprocessing_artifacts.pkl"

        split_data, artifacts = preprocess_pipeline(
            df=df,
            target_col=args.target,
            test_size=args.test_size,
            random_state=args.random_state,
            artifacts_path=artifacts_path,
        )

        # Save processed data
        train_path = output_dir / "train.csv"
        test_path = output_dir / "test.csv"

        split_data.train.to_csv(train_path, index=False)
        split_data.test.to_csv(test_path, index=False)

        print(f"\n✓ Training data saved to: {train_path}")
        print(f"✓ Test data saved to: {test_path}")
        print(f"✓ Preprocessing artifacts saved to: {artifacts_path}")

        # Print summary
        print("\n" + "=" * 80)
        print("PREPROCESSING SUMMARY")
        print("=" * 80)
        print(f"Input shape: {df.shape}")
        print(f"Train shape: {split_data.train.shape}")
        print(f"Test shape: {split_data.test.shape}")
        print(f"Features: {artifacts.metadata['n_features']}")
        print(f"Target column: {artifacts.metadata['target_col']}")
        print(f"Dropped columns: {len(artifacts.metadata['dropped_cols'])}")

        if artifacts.target_encoder:
            print(f"\nTarget classes: {list(artifacts.target_encoder.classes_)}")

        print("\n" + "=" * 80)
        print("Preprocessing complete! Ready for model training.")
        print("=" * 80)

    except FileNotFoundError as e:
        print("\n" + "=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        print("\nPlease ensure the dataset has been downloaded.")
        print("Run: python scripts/download_data.py")
        sys.exit(1)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
