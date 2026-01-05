from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV dataset.

    Args:
        path: Path to the CSV file

    Returns:
        DataFrame containing the loaded data

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")
    return pd.read_csv(path)


def load_diabetes_dataset(data_dir: str | Path = "data/raw") -> pd.DataFrame:
    """Load the Kaggle diabetes dataset.

    This function looks for the diabetic_data.csv file in the specified directory.

    Args:
        data_dir: Directory containing the raw data

    Returns:
        DataFrame containing the diabetes dataset

    Raises:
        FileNotFoundError: If the dataset file is not found
    """
    data_dir = Path(data_dir)
    possible_files = [
        data_dir / "diabetic_data.csv",
        data_dir / "diabetes.csv",
        data_dir / "data.csv",
    ]

    for file_path in possible_files:
        if file_path.exists():
            print(f"Loading dataset from: {file_path}")
            return pd.read_csv(file_path)

    raise FileNotFoundError(
        f"Dataset not found in {data_dir}. "
        f"Please download from https://www.kaggle.com/datasets/brandao/diabetes"
    )


def download_kaggle_dataset(
    dataset_name: str = "brandao/diabetes",
    output_dir: str | Path = "data/raw",
    force: bool = False,
) -> Path:
    """Download dataset from Kaggle using the Kaggle API.

    Args:
        dataset_name: Kaggle dataset identifier
        output_dir: Directory to save the downloaded data
        force: Force re-download even if file exists

    Returns:
        Path to the downloaded dataset directory

    Raises:
        ImportError: If kaggle package is not installed
        Exception: If download fails
    """
    try:
        import kaggle
    except ImportError:
        raise ImportError(
            "Kaggle package not installed. Install with: pip install kaggle\n"
            "Also ensure you have set up Kaggle API credentials: "
            "https://github.com/Kaggle/kaggle-api#api-credentials"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if dataset already exists
    if not force:
        for file_path in output_dir.glob("*.csv"):
            print(f"Dataset already exists at: {file_path}")
            return output_dir

    print(f"Downloading {dataset_name} to {output_dir}...")
    kaggle.api.dataset_download_files(
        dataset_name, path=str(output_dir), unzip=True
    )
    print("Download complete!")

    return output_dir
