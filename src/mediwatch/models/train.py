from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False


@dataclass(frozen=True)
class TrainArtifacts:
    """Container for training artifacts."""
    pipeline: Pipeline
    model_name: str
    params: Dict[str, Any]
    training_time: float


def get_baseline_models() -> Dict[str, Any]:
    """Get dictionary of baseline models with default parameters.
    
    Returns:
        Dictionary mapping model names to (model_class, default_params)
    """
    models = {
        "logistic_regression": (
            LogisticRegression,
            {
                "max_iter": 1000,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
        ),
        "random_forest": (
            RandomForestClassifier,
            {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
            }
        ),
        "gradient_boosting": (
            GradientBoostingClassifier,
            {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
                "random_state": 42,
            }
        ),
    }
    
    if XGBOOST_AVAILABLE:
        models["xgboost"] = (
            xgb.XGBClassifier,
            {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "min_child_weight": 1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
                "n_jobs": -1,
                "use_label_encoder": False,
                "eval_metric": "logloss",
            }
        )
    
    if LIGHTGBM_AVAILABLE:
        models["lightgbm"] = (
            lgb.LGBMClassifier,
            {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6,
                "num_leaves": 31,
                "min_child_samples": 20,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "random_state": 42,
                "n_jobs": -1,
                "class_weight": "balanced",
                "verbose": -1,
            }
        )
    
    if CATBOOST_AVAILABLE:
        models["catboost"] = (
            cb.CatBoostClassifier,
            {
                "iterations": 100,
                "learning_rate": 0.1,
                "depth": 6,
                "random_state": 42,
                "verbose": False,
                "auto_class_weights": "Balanced",
            }
        )
    
    return models


def train_model(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    model_name: str = "random_forest",
    model_params: Optional[Dict[str, Any]] = None,
    use_scaling: bool = True,
    track_mlflow: bool = True,
    experiment_name: str = "mediwatch-readmission",
) -> TrainArtifacts:
    """Train a classification model with optional MLflow tracking.
    
    Args:
        x_train: Training features
        y_train: Training labels
        model_name: Name of the model to train
        model_params: Model hyperparameters (overrides defaults)
        use_scaling: Whether to apply standard scaling
        track_mlflow: Whether to log to MLflow
        experiment_name: MLflow experiment name
        
    Returns:
        TrainArtifacts containing trained pipeline and metadata
    """
    start_time = time.time()
    
    # Get model class and default params
    available_models = get_baseline_models()
    
    if model_name not in available_models:
        raise ValueError(
            f"Model {model_name} not available. "
            f"Choose from: {list(available_models.keys())}"
        )
    
    model_class, default_params = available_models[model_name]
    
    # Merge default params with user-provided params
    params = default_params.copy()
    if model_params:
        params.update(model_params)
    
    # Create model
    model = model_class(**params)
    
    # Create pipeline
    steps = []
    if use_scaling:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", model))
    
    pipeline = Pipeline(steps=steps)
    
    # MLflow tracking
    if track_mlflow:
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=f"{model_name}_baseline"):
            # Log parameters
            mlflow.log_params({f"model_{k}": v for k, v in params.items()})
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("use_scaling", use_scaling)
            mlflow.log_param("n_features", x_train.shape[1])
            mlflow.log_param("n_samples", x_train.shape[0])
            
            # Train model
            pipeline.fit(x_train, y_train)
            
            training_time = time.time() - start_time
            mlflow.log_metric("training_time", training_time)
            
            # Log model
            mlflow.sklearn.log_model(
                pipeline,
                artifact_path="model",
                registered_model_name=f"mediwatch_{model_name}",
            )
            
            print(f"✓ Trained {model_name} in {training_time:.2f}s")
            print(f"  MLflow run ID: {mlflow.active_run().info.run_id}")
    else:
        # Train without MLflow
        pipeline.fit(x_train, y_train)
        training_time = time.time() - start_time
        print(f"✓ Trained {model_name} in {training_time:.2f}s")
    
    return TrainArtifacts(
        pipeline=pipeline,
        model_name=model_name,
        params=params,
        training_time=training_time,
    )


def train_baseline(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    preprocessor: ColumnTransformer | None = None,
) -> TrainArtifacts:
    """Train a baseline logistic regression model.
    
    Legacy function for backward compatibility.
    Use train_model() for more options.
    """
    if preprocessor is None:
        preprocessor = ColumnTransformer([], remainder="passthrough")

    clf = LogisticRegression(max_iter=500, random_state=42)
    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", clf)])
    
    start_time = time.time()
    pipeline.fit(x_train, y_train)
    training_time = time.time() - start_time
    
    return TrainArtifacts(
        pipeline=pipeline,
        model_name="logistic_regression",
        params={"max_iter": 500},
        training_time=training_time,
    )


def train_all_baselines(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    use_scaling: bool = True,
    track_mlflow: bool = True,
    experiment_name: str = "mediwatch-readmission",
) -> Dict[str, TrainArtifacts]:
    """Train all available baseline models.
    
    Args:
        x_train: Training features
        y_train: Training labels
        use_scaling: Whether to apply standard scaling
        track_mlflow: Whether to log to MLflow
        experiment_name: MLflow experiment name
        
    Returns:
        Dictionary mapping model names to TrainArtifacts
    """
    available_models = get_baseline_models()
    results = {}
    
    print("=" * 80)
    print(f"Training {len(available_models)} baseline models...")
    print("=" * 80)
    
    for model_name in available_models.keys():
        try:
            print(f"\nTraining {model_name}...")
            artifacts = train_model(
                x_train=x_train,
                y_train=y_train,
                model_name=model_name,
                use_scaling=use_scaling,
                track_mlflow=track_mlflow,
                experiment_name=experiment_name,
            )
            results[model_name] = artifacts
        except Exception as e:
            print(f"✗ Error training {model_name}: {e}")
    
    print("\n" + "=" * 80)
    print(f"Completed training {len(results)}/{len(available_models)} models")
    print("=" * 80)
    
    return results


def save_pipeline(pipeline: Pipeline, path: str | Path) -> None:
    """Save trained pipeline to disk.
    
    Args:
        pipeline: Trained sklearn pipeline
        path: Output file path
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)
    print(f"✓ Pipeline saved to: {path}")


def load_pipeline(path: str | Path) -> Pipeline:
    """Load trained pipeline from disk.
    
    Args:
        path: Path to saved pipeline
        
    Returns:
        Loaded pipeline
    """
    return joblib.load(path)
