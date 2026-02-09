import os
import sys
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import json
import mlflow
import mlflow.sklearn
from datetime import datetime

print("=" * 60)
print("🚀 MediWatch Model Training with MLflow")
print("=" * 60)

# Configure MLflow
mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mediwatch.svc.cluster.local:5000")
mlflow.set_tracking_uri(mlflow_uri)
mlflow.set_experiment("mediwatch_readmission_prediction")

print(f"\n🔗 MLflow Tracking URI: {mlflow_uri}")

# Start MLflow run
with mlflow.start_run(run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
    print(f"\n📝 MLflow Run ID: {run.info.run_id}")
    
    # Load data
    print("\n📥 Loading training data...")
    train_data = pd.read_csv("/data/processed/train.csv")
    test_data = pd.read_csv("/data/processed/test.csv")
    
    print(f"Training samples: {len(train_data)}")
    print(f"Test samples: {len(test_data)}")
    
    # Log dataset info
    mlflow.log_param("train_samples", len(train_data))
    mlflow.log_param("test_samples", len(test_data))
    
    # Prepare features
    target_col = "readmitted"
    X_train = train_data.drop(columns=[target_col])
    y_train = train_data[target_col]
    X_test = test_data.drop(columns=[target_col])
    y_test = test_data[target_col]
    
    n_features = X_train.shape[1]
    print(f"\n🔧 Features: {n_features}")
    mlflow.log_param("n_features", n_features)
    
    # Model hyperparameters
    params = {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 5,
        "random_state": 42
    }
    
    # Log hyperparameters
    for param, value in params.items():
        mlflow.log_param(param, value)
    
    # Train model
    print("\n🤖 Training Gradient Boosting model...")
    model = GradientBoostingClassifier(**params)
    
    model.fit(X_train, y_train)
    print("✅ Model training complete")
    
    # Evaluate
    print("\n📊 Evaluating model...")
    y_pred = model.predict(X_test)
    
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    }
    
    print("\nMetrics:")
    for metric, value in metrics.items():
        print(f"  • {metric}: {value:.4f}")
        mlflow.log_metric(metric, value)
    
    # Log model to MLflow
    print("\n📦 Logging model to MLflow...")
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="MediWatch_Readmission_Predictor"
    )
    print("✅ Model logged to MLflow")
    
    # Save model locally (for backward compatibility)
    print("\n💾 Saving model to local storage...")
    joblib.dump(model, "/models/Gradient_Boosting.pkl")
    print("✅ Model saved to /models/Gradient_Boosting.pkl")
    
    # Save metrics
    metrics_with_run = metrics.copy()
    metrics_with_run["mlflow_run_id"] = run.info.run_id
    metrics_with_run["mlflow_experiment_id"] = run.info.experiment_id
    
    with open("/models/metrics.json", "w") as f:
        json.dump(metrics_with_run, f, indent=2)
    
    # Log metrics file as artifact
    mlflow.log_artifact("/models/metrics.json")
    
    print("\n" + "=" * 60)
    print("✅ Training Complete!")
    print(f"📊 View in MLflow: {mlflow_uri}/#/experiments/{run.info.experiment_id}/runs/{run.info.run_id}")
    print("=" * 60)

sys.exit(0)
