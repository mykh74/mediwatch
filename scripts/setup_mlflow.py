#!/usr/bin/env python3
"""
MLflow setup and initialization script.

This script:
1. Initializes MLflow tracking server
2. Creates experiment for MediWatch
3. Sets up model registry
4. Provides utilities for MLflow management

Usage:
    python scripts/setup_mlflow.py --start
    python scripts/setup_mlflow.py --stop
    python scripts/setup_mlflow.py --init-experiment
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


def start_mlflow_server(
    backend_store_uri: str = "sqlite:///mlflow.db",
    default_artifact_root: str = "./mlruns",
    host: str = "127.0.0.1",
    port: int = 5000,
):
    """Start MLflow tracking server."""
    print("=" * 80)
    print("Starting MLflow Tracking Server")
    print("=" * 80)
    
    # Create directories if needed
    Path(default_artifact_root).mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "mlflow",
        "server",
        "--backend-store-uri", backend_store_uri,
        "--default-artifact-root", default_artifact_root,
        "--host", host,
        "--port", str(port),
    ]
    
    print(f"\nCommand: {' '.join(cmd)}")
    print(f"\nMLflow UI will be available at: http://{host}:{port}")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 80)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nMLflow server stopped.")


def init_experiment(
    experiment_name: str = "mediwatch-readmission",
    tracking_uri: str = "http://127.0.0.1:5000",
):
    """Initialize MLflow experiment."""
    mlflow.set_tracking_uri(tracking_uri)
    
    print("=" * 80)
    print("Initializing MLflow Experiment")
    print("=" * 80)
    
    try:
        # Create experiment if it doesn't exist
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                experiment_name,
                tags={
                    "project": "MediWatch",
                    "task": "patient-readmission-prediction",
                    "version": "1.0",
                },
            )
            print(f"\n✓ Created new experiment: {experiment_name}")
            print(f"  Experiment ID: {experiment_id}")
        else:
            print(f"\n✓ Experiment already exists: {experiment_name}")
            print(f"  Experiment ID: {experiment.experiment_id}")
        
        # Set as default
        mlflow.set_experiment(experiment_name)
        print(f"\n✓ Set as default experiment")
        
        # Display info
        client = MlflowClient()
        exp = client.get_experiment_by_name(experiment_name)
        print(f"\nExperiment Details:")
        print(f"  Name: {exp.name}")
        print(f"  ID: {exp.experiment_id}")
        print(f"  Artifact Location: {exp.artifact_location}")
        print(f"  Lifecycle Stage: {exp.lifecycle_stage}")
        
        print("\n" + "=" * 80)
        print("Experiment initialized successfully!")
        print(f"Access MLflow UI at: {tracking_uri}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error initializing experiment: {e}")
        sys.exit(1)


def list_experiments(tracking_uri: str = "http://127.0.0.1:5000"):
    """List all MLflow experiments."""
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    print("=" * 80)
    print("MLflow Experiments")
    print("=" * 80)
    
    experiments = client.search_experiments()
    
    if not experiments:
        print("\nNo experiments found.")
    else:
        for exp in experiments:
            print(f"\nExperiment: {exp.name}")
            print(f"  ID: {exp.experiment_id}")
            print(f"  Artifact Location: {exp.artifact_location}")
            print(f"  Lifecycle Stage: {exp.lifecycle_stage}")
            
            # Count runs
            runs = client.search_runs(exp.experiment_id)
            print(f"  Total Runs: {len(runs)}")


def setup_model_registry(tracking_uri: str = "http://127.0.0.1:5000"):
    """Verify model registry is accessible."""
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    print("=" * 80)
    print("MLflow Model Registry")
    print("=" * 80)
    
    try:
        # Try to list registered models
        models = client.search_registered_models()
        print(f"\n✓ Model registry is accessible")
        print(f"  Registered models: {len(models)}")
        
        if models:
            print("\nRegistered Models:")
            for model in models:
                print(f"  - {model.name}")
                print(f"    Latest version: {model.latest_versions[0].version if model.latest_versions else 'N/A'}")
        else:
            print("\n  No models registered yet.")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error accessing model registry: {e}")
        print("\nNote: Model registry requires a database backend store.")
        print("Current backend: SQLite (basic registry support)")


def main():
    parser = argparse.ArgumentParser(
        description="MLflow setup and management for MediWatch"
    )
    parser.add_argument(
        "--action",
        choices=["start", "init", "list", "registry"],
        default="init",
        help="Action to perform",
    )
    parser.add_argument(
        "--tracking-uri",
        type=str,
        default="http://127.0.0.1:5000",
        help="MLflow tracking URI",
    )
    parser.add_argument(
        "--backend-store",
        type=str,
        default="sqlite:///mlflow.db",
        help="Backend store URI",
    )
    parser.add_argument(
        "--artifact-root",
        type=str,
        default="./mlruns",
        help="Default artifact root",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Server port",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default="mediwatch-readmission",
        help="Experiment name",
    )
    
    args = parser.parse_args()
    
    if args.action == "start":
        start_mlflow_server(
            backend_store_uri=args.backend_store,
            default_artifact_root=args.artifact_root,
            host=args.host,
            port=args.port,
        )
    elif args.action == "init":
        init_experiment(
            experiment_name=args.experiment_name,
            tracking_uri=args.tracking_uri,
        )
    elif args.action == "list":
        list_experiments(tracking_uri=args.tracking_uri)
    elif args.action == "registry":
        setup_model_registry(tracking_uri=args.tracking_uri)


if __name__ == "__main__":
    main()
