from __future__ import annotations

"""MLflow registry helpers for model management.

This module provides utilities for:
- Setting up MLflow tracking
- Managing experiments
- Logging models and artifacts
- Selecting best models
- Promoting models to production
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import mlflow
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
import pandas as pd


def setup_mlflow(
    tracking_uri: str = "http://127.0.0.1:5000",
    experiment_name: str = "mediwatch-readmission",
) -> str:
    """Set up MLflow tracking and experiment.
    
    Args:
        tracking_uri: MLflow tracking server URI
        experiment_name: Name of the experiment
        
    Returns:
        Experiment ID
    """
    mlflow.set_tracking_uri(tracking_uri)
    
    # Get or create experiment
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name,
            tags={
                "project": "MediWatch",
                "task": "patient-readmission-prediction",
            },
        )
    else:
        experiment_id = experiment.experiment_id
    
    mlflow.set_experiment(experiment_name)
    
    return experiment_id


def log_preprocessing_artifacts(
    artifacts_path: str | Path,
    artifact_path: str = "preprocessing",
) -> None:
    """Log preprocessing artifacts to MLflow.
    
    Args:
        artifacts_path: Path to preprocessing artifacts file
        artifact_path: Path within MLflow artifacts
    """
    if mlflow.active_run():
        mlflow.log_artifact(str(artifacts_path), artifact_path=artifact_path)


def get_best_run(
    experiment_name: str = "mediwatch-readmission",
    metric: str = "test_f1",
    tracking_uri: str = "http://127.0.0.1:5000",
) -> Optional[mlflow.entities.Run]:
    """Get the best run from an experiment based on a metric.
    
    Args:
        experiment_name: Name of the experiment
        metric: Metric to optimize (e.g., 'test_f1', 'test_roc_auc')
        tracking_uri: MLflow tracking server URI
        
    Returns:
        Best run or None if no runs found
    """
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    # Get experiment
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        print(f"Experiment '{experiment_name}' not found")
        return None
    
    # Search for runs
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1000,
        order_by=[f"metrics.{metric} DESC"],
    )
    
    if not runs:
        print(f"No runs found in experiment '{experiment_name}'")
        return None
    
    best_run = runs[0]
    
    print(f"Best run based on {metric}:")
    print(f"  Run ID: {best_run.info.run_id}")
    print(f"  {metric}: {best_run.data.metrics.get(metric, 'N/A')}")
    
    return best_run


def select_best_model(
    experiment_name: str = "mediwatch-readmission",
    metric: str = "test_f1",
    tracking_uri: str = "http://127.0.0.1:5000",
) -> Tuple[Optional[str], Optional[mlflow.entities.Run]]:
    """Select and load the best model from an experiment.
    
    Args:
        experiment_name: Name of the experiment
        metric: Metric to optimize
        tracking_uri: MLflow tracking server URI
        
    Returns:
        Tuple of (model_uri, run) or (None, None) if not found
    """
    best_run = get_best_run(experiment_name, metric, tracking_uri)
    
    if best_run is None:
        return None, None
    
    # Construct model URI
    model_uri = f"runs:/{best_run.info.run_id}/model"
    
    return model_uri, best_run


def load_best_model(
    experiment_name: str = "mediwatch-readmission",
    metric: str = "test_f1",
    tracking_uri: str = "http://127.0.0.1:5000",
):
    """Load the best model from an experiment.
    
    Args:
        experiment_name: Name of the experiment
        metric: Metric to optimize
        tracking_uri: MLflow tracking server URI
        
    Returns:
        Loaded model or None
    """
    model_uri, run = select_best_model(experiment_name, metric, tracking_uri)
    
    if model_uri is None:
        return None
    
    try:
        model = mlflow.sklearn.load_model(model_uri)
        print(f"✓ Loaded model from run {run.info.run_id}")
        return model
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return None


def register_model(
    model_uri: str,
    model_name: str,
    tags: Optional[Dict[str, str]] = None,
    description: Optional[str] = None,
) -> mlflow.entities.model_registry.ModelVersion:
    """Register a model in MLflow Model Registry.
    
    Args:
        model_uri: URI of the model (e.g., 'runs:/run_id/model')
        model_name: Name for the registered model
        tags: Optional tags for the model version
        description: Optional description
        
    Returns:
        Registered model version
    """
    try:
        model_version = mlflow.register_model(model_uri, model_name)
        
        if tags or description:
            client = MlflowClient()
            
            if tags:
                for key, value in tags.items():
                    client.set_model_version_tag(
                        model_name, model_version.version, key, value
                    )
            
            if description:
                client.update_model_version(
                    name=model_name,
                    version=model_version.version,
                    description=description,
                )
        
        print(f"✓ Registered model '{model_name}' version {model_version.version}")
        return model_version
        
    except Exception as e:
        print(f"✗ Error registering model: {e}")
        raise


def promote_model_to_production(
    model_name: str,
    version: Optional[int] = None,
    tracking_uri: str = "http://127.0.0.1:5000",
) -> None:
    """Promote a model version to Production stage.
    
    Args:
        model_name: Name of the registered model
        version: Model version (uses latest if None)
        tracking_uri: MLflow tracking server URI
    """
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    try:
        # Get latest version if not specified
        if version is None:
            versions = client.search_model_versions(f"name='{model_name}'")
            if not versions:
                print(f"No versions found for model '{model_name}'")
                return
            version = max(int(v.version) for v in versions)
        
        # Transition to Production
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True,
        )
        
        print(f"✓ Promoted {model_name} v{version} to Production")
        
    except Exception as e:
        print(f"✗ Error promoting model: {e}")


def compare_runs(
    experiment_name: str = "mediwatch-readmission",
    metrics: List[str] = None,
    tracking_uri: str = "http://127.0.0.1:5000",
) -> pd.DataFrame:
    """Compare all runs in an experiment.
    
    Args:
        experiment_name: Name of the experiment
        metrics: List of metrics to include (all if None)
        tracking_uri: MLflow tracking server URI
        
    Returns:
        DataFrame with run comparisons
    """
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        print(f"Experiment '{experiment_name}' not found")
        return pd.DataFrame()
    
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
    )
    
    if not runs:
        print(f"No runs found in experiment '{experiment_name}'")
        return pd.DataFrame()
    
    data = []
    for run in runs:
        row = {
            "run_id": run.info.run_id,
            "run_name": run.data.tags.get("mlflow.runName", ""),
            "status": run.info.status,
            "start_time": pd.to_datetime(run.info.start_time, unit='ms'),
        }
        
        # Add metrics
        if metrics:
            for metric in metrics:
                row[metric] = run.data.metrics.get(metric)
        else:
            row.update(run.data.metrics)
        
        # Add key parameters
        row.update({f"param_{k}": v for k, v in run.data.params.items()})
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Sort by first metric if available
    if metrics and metrics[0] in df.columns:
        df = df.sort_values(metrics[0], ascending=False)
    
    return df
