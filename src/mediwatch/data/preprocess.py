from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


@dataclass(frozen=True)
class SplitData:
    train: pd.DataFrame
    test: pd.DataFrame


@dataclass
class PreprocessingArtifacts:
    """Container for preprocessing artifacts to be reused during inference."""

    label_encoders: Dict[str, LabelEncoder]
    scaler: Optional[StandardScaler]
    feature_names: List[str]
    target_encoder: Optional[LabelEncoder]
    metadata: Dict[str, Any]

    def save(self, path: str | Path) -> None:
        """Save preprocessing artifacts to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Preprocessing artifacts saved to: {path}")

    @classmethod
    def load(cls, path: str | Path) -> "PreprocessingArtifacts":
        """Load preprocessing artifacts from disk."""
        with open(path, "rb") as f:
            return pickle.load(f)


def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning of the diabetes dataset.

    Handles:
    - Replacing '?' with NaN
    - Replacing other special missing value indicators
    - Removing duplicates

    Args:
        df: Raw dataframe

    Returns:
        Cleaned dataframe
    """
    df_clean = df.copy()

    # Replace '?' with NaN (common in diabetes dataset)
    df_clean.replace("?", np.nan, inplace=True)

    # Replace other special values that represent missing data
    special_values = ["Unknown", "unknown", "UNKNOWN", "None", "NA", "N/A", ""]
    for val in special_values:
        df_clean.replace(val, np.nan, inplace=True)

    # Remove duplicates
    n_duplicates = df_clean.duplicated().sum()
    if n_duplicates > 0:
        print(f"Removing {n_duplicates} duplicate rows...")
        df_clean.drop_duplicates(inplace=True)

    return df_clean


def handle_missing_values(
    df: pd.DataFrame, threshold: float = 0.5
) -> Tuple[pd.DataFrame, List[str]]:
    """Handle missing values in the dataset.

    Strategy:
    - Drop columns with >threshold% missing values
    - Impute numerical columns with median
    - Impute categorical columns with mode

    Args:
        df: DataFrame with potential missing values
        threshold: Threshold for dropping columns (0-1)

    Returns:
        Tuple of (cleaned DataFrame, list of dropped columns)
    """
    df_clean = df.copy()
    dropped_cols = []

    # Drop columns with high missing percentage
    for col in df_clean.columns:
        missing_pct = df_clean[col].isnull().sum() / len(df_clean)
        if missing_pct > threshold:
            dropped_cols.append(col)
            df_clean.drop(columns=[col], inplace=True)
            print(f"Dropped column '{col}' ({missing_pct * 100:.1f}% missing)")

    # Impute remaining missing values
    for col in df_clean.columns:
        if df_clean[col].isnull().sum() > 0:
            if df_clean[col].dtype in ["int64", "float64"]:
                # Numerical: impute with median
                median_val = df_clean[col].median()
                df_clean[col].fillna(median_val, inplace=True)
            else:
                # Categorical: impute with mode
                mode_val = (
                    df_clean[col].mode()[0]
                    if not df_clean[col].mode().empty
                    else "Unknown"
                )
                df_clean[col].fillna(mode_val, inplace=True)

    return df_clean, dropped_cols


def encode_categorical_features(
    df: pd.DataFrame,
    target_col: Optional[str] = None,
    label_encoders: Optional[Dict[str, LabelEncoder]] = None,
) -> Tuple[pd.DataFrame, Dict[str, LabelEncoder]]:
    """Encode categorical features.

    Strategy:
    - Binary features: Label encoding
    - Low cardinality (<=10): One-hot encoding
    - High cardinality (>10): Label encoding

    Args:
        df: DataFrame with categorical features
        target_col: Name of target column to exclude from encoding
        label_encoders: Pre-fitted label encoders for inference (optional)

    Returns:
        Tuple of (encoded DataFrame, dictionary of label encoders)
    """
    df_encoded = df.copy()
    is_training = label_encoders is None
    if label_encoders is None:
        label_encoders = {}

    categorical_cols = df_encoded.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    # Remove target column from encoding
    if target_col and target_col in categorical_cols:
        categorical_cols.remove(target_col)

    for col in categorical_cols:
        n_unique = df_encoded[col].nunique()

        if n_unique <= 2:
            # Binary encoding
            if is_training:
                le = LabelEncoder()
                df_encoded[f"{col}_encoded"] = le.fit_transform(
                    df_encoded[col].astype(str)
                )
                label_encoders[col] = le
            else:
                # Use existing encoder
                le = label_encoders.get(col)
                if le:
                    # Handle unseen categories
                    df_encoded[f"{col}_encoded"] = df_encoded[col].apply(
                        lambda x: (
                            le.transform([str(x)])[0]
                            if str(x) in le.classes_
                            else -1
                        )
                    )
        elif n_unique <= 10:
            # One-hot encoding for low cardinality
            if is_training:
                dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
                df_encoded = pd.concat([df_encoded, dummies], axis=1)
                # Store dummy column names for inference
                label_encoders[f"{col}_dummies"] = dummies.columns.tolist()
            else:
                # Use existing dummy columns
                dummy_cols = label_encoders.get(f"{col}_dummies", [])
                dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
                # Ensure same columns as training
                for dummy_col in dummy_cols:
                    if dummy_col not in dummies.columns:
                        dummies[dummy_col] = 0
                df_encoded = pd.concat([df_encoded, dummies[dummy_cols]], axis=1)
        else:
            # Label encoding for high cardinality
            if is_training:
                le = LabelEncoder()
                df_encoded[f"{col}_encoded"] = le.fit_transform(
                    df_encoded[col].astype(str)
                )
                label_encoders[col] = le
            else:
                le = label_encoders.get(col)
                if le:
                    df_encoded[f"{col}_encoded"] = df_encoded[col].apply(
                        lambda x: (
                            le.transform([str(x)])[0]
                            if str(x) in le.classes_
                            else -1
                        )
                    )

    return df_encoded, label_encoders


def create_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features based on domain knowledge.

    Args:
        df: DataFrame with base features

    Returns:
        DataFrame with additional engineered features
    """
    df_eng = df.copy()

    # Count number of diagnoses
    diag_cols = [col for col in df_eng.columns if "diag" in col.lower()]
    if diag_cols:
        df_eng["num_diagnoses"] = df_eng[diag_cols].notna().sum(axis=1)

    # Procedures per day (if applicable)
    if "time_in_hospital" in df_eng.columns and "num_procedures" in df_eng.columns:
        df_eng["procedures_per_day"] = df_eng["num_procedures"] / (
            df_eng["time_in_hospital"] + 1
        )

    # Medications per diagnosis
    if "num_medications" in df_eng.columns and "num_diagnoses" in df_eng.columns:
        df_eng["meds_per_diagnosis"] = df_eng["num_medications"] / (
            df_eng["num_diagnoses"] + 1
        )

    # Lab procedures per day
    if "time_in_hospital" in df_eng.columns and "num_lab_procedures" in df_eng.columns:
        df_eng["lab_procedures_per_day"] = df_eng["num_lab_procedures"] / (
            df_eng["time_in_hospital"] + 1
        )

    return df_eng


def prepare_features_and_target(
    df: pd.DataFrame, target_col: str = "readmitted"
) -> Tuple[pd.DataFrame, pd.Series]:
    """Separate features and target, keeping only numerical features.

    Args:
        df: Preprocessed DataFrame
        target_col: Name of the target column

    Returns:
        Tuple of (feature DataFrame, target Series)
    """
    # Select only numerical columns as features
    feature_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()

    # Remove target if it's in feature columns
    if target_col in feature_cols:
        feature_cols.remove(target_col)

    # Also remove ID columns
    id_cols = [col for col in feature_cols if "id" in col.lower()]
    for col in id_cols:
        if col in feature_cols:
            feature_cols.remove(col)

    X = df[feature_cols].copy()
    y = df[target_col].copy() if target_col in df.columns else None

    return X, y


def preprocess_pipeline(
    df: pd.DataFrame,
    target_col: str = "readmitted",
    test_size: float = 0.2,
    random_state: int = 42,
    artifacts_path: Optional[str | Path] = None,
) -> Tuple[SplitData, PreprocessingArtifacts]:
    """Complete preprocessing pipeline for training.

    Args:
        df: Raw DataFrame
        target_col: Name of target column
        test_size: Proportion of data for test set
        random_state: Random seed for reproducibility
        artifacts_path: Path to save preprocessing artifacts

    Returns:
        Tuple of (train/test split, preprocessing artifacts)
    """
    print("Starting preprocessing pipeline...")

    # Step 1: Basic cleaning
    print("\n1. Basic cleaning...")
    df_clean = basic_clean(df)

    # Step 2: Handle missing values
    print("\n2. Handling missing values...")
    df_clean, dropped_cols = handle_missing_values(df_clean, threshold=0.5)

    # Step 3: Feature engineering
    print("\n3. Creating derived features...")
    df_eng = create_derived_features(df_clean)

    # Step 4: Encode categorical features
    print("\n4. Encoding categorical features...")
    df_encoded, label_encoders = encode_categorical_features(
        df_eng, target_col=target_col
    )

    # Step 5: Prepare features and target
    print("\n5. Preparing features and target...")
    X, y = prepare_features_and_target(df_encoded, target_col=target_col)

    # Encode target if categorical
    target_encoder = None
    if y is not None and y.dtype == "object":
        target_encoder = LabelEncoder()
        y = pd.Series(target_encoder.fit_transform(y), name=target_col)

    # Step 6: Split data
    print("\n6. Splitting data...")
    if y is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
    else:
        # No target available, just split X
        X_train, X_test = train_test_split(
            X, test_size=test_size, random_state=random_state
        )
        y_train = y_test = None

    # Create split data with target included
    train_df = X_train.copy()
    test_df = X_test.copy()
    if y_train is not None:
        train_df[target_col] = y_train.values
        test_df[target_col] = y_test.values

    split_data = SplitData(train=train_df, test=test_df)

    # Step 7: Create artifacts
    print("\n7. Creating preprocessing artifacts...")
    artifacts = PreprocessingArtifacts(
        label_encoders=label_encoders,
        scaler=None,  # Can add StandardScaler if needed
        feature_names=X.columns.tolist(),
        target_encoder=target_encoder,
        metadata={
            "target_col": target_col,
            "dropped_cols": dropped_cols,
            "n_features": len(X.columns),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        },
    )

    # Save artifacts if path provided
    if artifacts_path:
        artifacts.save(artifacts_path)

    print("\nPreprocessing complete!")
    print(f"Train set: {X_train.shape}")
    print(f"Test set: {X_test.shape}")
    print(f"Features: {len(X.columns)}")

    return split_data, artifacts


def apply_preprocessing(
    df: pd.DataFrame,
    artifacts: PreprocessingArtifacts,
    target_col: Optional[str] = None,
) -> pd.DataFrame:
    """Apply preprocessing using saved artifacts (for inference).

    Args:
        df: Raw DataFrame
        artifacts: Preprocessing artifacts from training
        target_col: Optional target column name

    Returns:
        Preprocessed DataFrame
    """
    # Basic cleaning
    df_clean = basic_clean(df)

    # Drop columns that were dropped during training
    dropped_cols = artifacts.metadata.get("dropped_cols", [])
    df_clean = df_clean.drop(
        columns=[col for col in dropped_cols if col in df_clean.columns],
        errors="ignore",
    )

    # Feature engineering
    df_eng = create_derived_features(df_clean)

    # Encode categorical features using saved encoders
    df_encoded, _ = encode_categorical_features(
        df_eng, target_col=target_col, label_encoders=artifacts.label_encoders
    )

    # Select only the features that were used during training
    feature_cols = [col for col in artifacts.feature_names if col in df_encoded.columns]
    missing_cols = set(artifacts.feature_names) - set(feature_cols)

    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
        # Add missing columns with default value
        for col in missing_cols:
            df_encoded[col] = 0

    # Return features in the same order as training
    return df_encoded[artifacts.feature_names]
