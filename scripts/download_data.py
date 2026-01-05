#!/usr/bin/env python3
"""
Script to download the diabetes dataset from Kaggle.

Usage:
    python scripts/download_data.py
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mediwatch.data.load import download_kaggle_dataset, load_diabetes_dataset


def main():
    parser = argparse.ArgumentParser(
        description="Download the diabetes dataset from Kaggle"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="brandao/diabetes",
        help="Kaggle dataset identifier (default: brandao/diabetes)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for downloaded data (default: data/raw)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if data exists",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the downloaded dataset can be loaded",
    )

    args = parser.parse_args()

    try:
        # Download dataset
        print("=" * 80)
        print("MediWatch Dataset Download")
        print("=" * 80)

        output_path = download_kaggle_dataset(
            dataset_name=args.dataset,
            output_dir=args.output_dir,
            force=args.force,
        )

        print(f"\n✓ Dataset downloaded successfully to: {output_path}")

        # Verify if requested
        if args.verify:
            print("\nVerifying dataset...")
            df = load_diabetes_dataset(data_dir=args.output_dir)
            print(f"✓ Dataset loaded successfully!")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {df.shape[1]}")
            print(f"  Rows: {df.shape[0]:,}")

            print("\nFirst few columns:")
            print(f"  {', '.join(df.columns[:5].tolist())}")

        print("\n" + "=" * 80)
        print("You can now proceed with the EDA notebook!")
        print("=" * 80)

    except ImportError as e:
        print("\n" + "=" * 80)
        print("ERROR: Kaggle API not installed or configured")
        print("=" * 80)
        print("\nPlease follow these steps:")
        print("1. Install kaggle: pip install kaggle")
        print("2. Create a Kaggle account at https://www.kaggle.com")
        print("3. Go to Kaggle → Account → API → Create New API Token")
        print("4. Place kaggle.json in ~/.kaggle/")
        print("5. Run: chmod 600 ~/.kaggle/kaggle.json")
        print("\nAlternatively, download manually from:")
        print("https://www.kaggle.com/datasets/brandao/diabetes")
        sys.exit(1)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        print("\nTroubleshooting:")
        print("- Ensure Kaggle API is properly configured")
        print("- Check your internet connection")
        print("- Verify dataset name is correct")
        print("- Try downloading manually from Kaggle website")
        sys.exit(1)


if __name__ == "__main__":
    main()
