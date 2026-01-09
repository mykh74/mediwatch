from __future__ import annotations

"""Hyperparameter tuning with Ray Tune and MLflow integration.

This module provides functions for large-scale hyperparameter optimization
using Ray Tune with MLflow tracking.
"""

import time
from typing import Any, Dict, Optional

import mlflow
import numpy as np
import pandas as pd
from ray import train, tune
from ray.tune.schedulers import ASHAScheduler
from ray.tune.search.optuna import OptunaSearch
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except (ImportError, Exception) as e:
    # Handle both import errors and library loading errors
    XGBOOST_AVAILABLE = False
    xgb = None

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except (ImportError, Exception) as e:
    # Handle both import errors and library loading errors
    LIGHTGBM_AVAILABLE = False
    lgb = None


def get_search_space(model_name: str) -> Dict[str, Any]:
    """Get Ray Tune search space for a given model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary defining the search space
    """
    if model_name == "logistic_regression":
        return {
            "C": tune.loguniform(0.001, 10.0),
            "penalty": tune.choice(["l1", "l2"]),
            "solver": tune.choice(["liblinear", "saga"]),
            "max_iter": tune.choice([500, 1000, 2000]),
        }
    
    elif model_name == "random_forest":
        return {
            "n_estimators": tune.choice([50, 100, 200, 300]),
            "max_depth": tune.choice([5, 10, 15, 20, None]),
            "min_samples_split": tune.choice([2, 5, 10]),
            "min_samples_leaf": tune.choice([1, 2, 4]),
            "max_features": tune.choice(["sqrt", "log2", None]),
        }
    
    elif model_name == "gradient_boosting":
        return {
            "n_estimators": tune.choice([50, 100, 200]),
            "learning_rate": tune.loguniform(0.01, 0.3),
            "max_depth": tune.choice([3, 5, 7, 9]),
            "min_samples_split": tune.choice([2, 5, 10]),
            "min_samples_leaf": tune.choice([1, 2, 4]),
            "subsample": tune.uniform(0.6, 1.0),
        }
    
    elif model_name == "xgboost" and XGBOOST_AVAILABLE:
        return {
            "n_estimators": tune.choice([50, 100, 200, 300]),
            "learning_rate": tune.loguniform(0.01, 0.3),
            "max_depth": tune.choice([3, 5, 7, 9, 11]),
            "min_child_weight": tune.choice([1, 3, 5, 7]),
            "subsample": tune.uniform(0.6, 1.0),
            "colsample_bytree": tune.uniform(0.6, 1.0),
            "gamma": tune.uniform(0, 0.5),
        }
    
    elif model_name == "lightgbm" and LIGHTGBM_AVAILABLE:
        return {
            "n_estimators": tune.choice([50, 100, 200, 300]),
            "learning_rate": tune.loguniform(0.01, 0.3),
            "max_depth": tune.choice([3, 5, 7, 9, 11]),
            "num_leaves": tune.choice([15, 31, 63, 127]),
            "min_child_samples": tune.choice([10, 20, 30, 50]),
            "subsample": tune.uniform(0.6, 1.0),
            "colsample_bytree": tune.uniform(0.6, 1.0),
        }
    
    else:
        raise ValueError(f"Unknown model name: {model_name}")


def create_model(model_name: str, config: Dict[str, Any]):
    """Create a model instance from config.
    
    Args:
        model_name: Name of the model
        config: Hyperparameters
        
    Returns:
        Model instance
    """
    base_params = {"random_state": 42}
    
    if model_name == "logistic_regression":
        return LogisticRegression(**{**base_params, **config, "n_jobs": -1})
    
    elif model_name == "random_forest":
        return RandomForestClassifier(**{**base_params, **config, "n_jobs": -1, "class_weight": "balanced"})
    
    elif model_name == "gradient_boosting":
        return GradientBoostingClassifier(**{**base_params, **config})
    
    elif model_name == "xgboost" and XGBOOST_AVAILABLE:
        return xgb.XGBClassifier(
            **{**base_params, **config, "n_jobs": -1, "use_label_encoder": False, "eval_metric": "logloss"}
        )
    
    elif model_name == "lightgbm" and LIGHTGBM_AVAILABLE:
        return lgb.LGBMClassifier(
            **{**base_params, **config, "n_jobs": -1, "class_weight": "balanced", "verbose": -1}
        )
    
    else:
        raise ValueError(f"Unknown model name: {model_name}")


def objective(
    config: Dict[str, Any],
    model_name: str,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    cv: int = 3,
    use_scaling: bool = True,
):
    """Objective function for Ray Tune.
    
    Args:
        config: Hyperparameter configuration from Ray Tune
        model_name: Name of the model
        x_train: Training features
        y_train: Training labels
        cv: Number of cross-validation folds
        use_scaling: Whether to use standard scaling
    """
    # Create model
    model = create_model(model_name, config)
    
    # Create pipeline
    steps = []
    if use_scaling:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", model))
    pipeline = Pipeline(steps=steps)
    
    # Cross-validation
    try:
        scores = cross_val_score(
            pipeline, x_train, y_train,
            cv=cv, scoring="f1_weighted", n_jobs=1
        )
        mean_score = scores.mean()
        std_score = scores.std()
        
        # Report metrics to Ray Tune
        train.report({"f1_score": mean_score, "f1_std": std_score})
        
    except Exception as e:
        print(f"Error in trial: {e}")
        train.report({"f1_score": 0.0, "f1_std": 1.0})


def run_hpo(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    model_name: str = "random_forest",
    num_samples: int = 20,
    max_concurrent_trials: int = 4,
    cv: int = 3,
    use_scaling: bool = True,
    mlflow_experiment_name: str = "mediwatch-readmission",
) -> Dict[str, Any]:
    """Run hyperparameter optimization using Ray Tune.
    
    Args:
        x_train: Training features
        y_train: Training labels
        model_name: Name of the model to tune
        num_samples: Number of trials to run
        max_concurrent_trials: Maximum number of concurrent trials
        cv: Number of cross-validation folds
        use_scaling: Whether to use standard scaling
        mlflow_experiment_name: MLflow experiment name for tracking
        
    Returns:
        Dictionary containing best config and results
    """
    print("=" * 80)
    print(f"Starting Hyperparameter Optimization for {model_name}")
    print("=" * 80)
    print(f"Number of trials: {num_samples}")
    print(f"Max concurrent: {max_concurrent_trials}")
    print(f"CV folds: {cv}")
    print("=" * 80)
    
    # Get search space
    search_space = get_search_space(model_name)
    
    # Configure scheduler (early stopping)
    scheduler = ASHAScheduler(
        max_t=cv,
        grace_period=1,
        reduction_factor=2,
    )
    
    # Configure search algorithm (Optuna for efficient search)
    search_alg = OptunaSearch()
    
    # Set up MLflow
    mlflow.set_experiment(mlflow_experiment_name)
    
    # Run tuning
    start_time = time.time()
    
    tuner = tune.Tuner(
        tune.with_parameters(
            objective,
            model_name=model_name,
            x_train=x_train,
            y_train=y_train,
            cv=cv,
            use_scaling=use_scaling,
        ),
        tune_config=tune.TuneConfig(
            metric="f1_score",
            mode="max",
            scheduler=scheduler,
            search_alg=search_alg,
            num_samples=num_samples,
            max_concurrent_trials=max_concurrent_trials,
        ),
        param_space=search_space,
    )
    
    results = tuner.fit()
    
    tuning_time = time.time() - start_time
    
    # Get best result
    best_result = results.get_best_result("f1_score", "max")
    best_config = best_result.config
    best_score = best_result.metrics["f1_score"]
    
    print("\n" + "=" * 80)
    print("Hyperparameter Optimization Complete!")
    print("=" * 80)
    print(f"Time taken: {tuning_time:.2f}s")
    print(f"Best F1 score: {best_score:.4f}")
    print(f"\nBest configuration:")
    for key, value in best_config.items():
        print(f"  {key}: {value}")
    print("=" * 80)
    
    # Log best result to MLflow
    with mlflow.start_run(run_name=f"{model_name}_best_hpo"):
        mlflow.log_params(best_config)
        mlflow.log_metric("cv_f1_score", best_score)
        mlflow.log_metric("tuning_time", tuning_time)
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("num_trials", num_samples)
        mlflow.log_param("cv_folds", cv)
    
    return {
        "best_config": best_config,
        "best_score": best_score,
        "tuning_time": tuning_time,
        "all_results": results,
    }


def tune_multiple_models(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    model_names: list[str] = None,
    num_samples: int = 20,
    max_concurrent_trials: int = 4,
    cv: int = 3,
    use_scaling: bool = True,
    mlflow_experiment_name: str = "mediwatch-readmission",
) -> Dict[str, Dict[str, Any]]:
    """Run HPO for multiple models.
    
    Args:
        x_train: Training features
        y_train: Training labels
        model_names: List of model names to tune
        num_samples: Number of trials per model
        max_concurrent_trials: Maximum number of concurrent trials
        cv: Number of cross-validation folds
        use_scaling: Whether to use standard scaling
        mlflow_experiment_name: MLflow experiment name
        
    Returns:
        Dictionary mapping model names to their best configs
    """
    if model_names is None:
        model_names = ["random_forest", "gradient_boosting"]
        if XGBOOST_AVAILABLE:
            model_names.append("xgboost")
        if LIGHTGBM_AVAILABLE:
            model_names.append("lightgbm")
    
    results = {}
    
    for model_name in model_names:
        try:
            print(f"\n{'='*80}")
            print(f"Tuning {model_name}...")
            print(f"{'='*80}\n")
            
            result = run_hpo(
                x_train=x_train,
                y_train=y_train,
                model_name=model_name,
                num_samples=num_samples,
                max_concurrent_trials=max_concurrent_trials,
                cv=cv,
                use_scaling=use_scaling,
                mlflow_experiment_name=mlflow_experiment_name,
            )
            results[model_name] = result
            
        except Exception as e:
            print(f"Error tuning {model_name}: {e}")
    
    return results
