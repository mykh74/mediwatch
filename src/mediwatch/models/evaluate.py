from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    classification_report,
    average_precision_score,
)
from sklearn.pipeline import Pipeline


@dataclass(frozen=True)
class Metrics:
    """Comprehensive metrics for classification evaluation."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    average_precision: float | None
    confusion_matrix: np.ndarray
    classification_report: str


def evaluate_model(
    pipeline: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    track_mlflow: bool = True,
    threshold: float = 0.5,
) -> Metrics:
    """Evaluate a trained model on test data.
    
    Args:
        pipeline: Trained sklearn pipeline
        x_test: Test features
        y_test: Test labels
        track_mlflow: Whether to log metrics to MLflow
        threshold: Classification threshold for binary prediction
        
    Returns:
        Metrics object containing evaluation results
    """
    # Get predictions
    y_pred_proba = pipeline.predict_proba(x_test)
    
    # Handle multi-class vs binary
    if y_pred_proba.shape[1] == 2:
        # Binary classification - use probability of positive class
        y_prob = y_pred_proba[:, 1]
    else:
        # Multi-class - use max probability
        y_prob = y_pred_proba.max(axis=1)
    
    y_pred = (y_prob >= threshold).astype(int)
    
    # Calculate metrics
    accuracy = float(accuracy_score(y_test, y_pred))
    
    # Handle multi-class with averaging
    average_method = 'binary' if len(np.unique(y_test)) == 2 else 'weighted'
    
    precision = float(precision_score(y_test, y_pred, average=average_method, zero_division=0))
    recall = float(recall_score(y_test, y_pred, average=average_method, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average=average_method, zero_division=0))
    
    # ROC AUC (only for binary or with multi-class averaging)
    try:
        if len(np.unique(y_test)) == 2:
            roc_auc = float(roc_auc_score(y_test, y_prob))
            avg_precision = float(average_precision_score(y_test, y_prob))
        else:
            # Multi-class ROC AUC
            roc_auc = float(roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted'))
            avg_precision = None
    except Exception as e:
        print(f"Warning: Could not calculate ROC AUC: {e}")
        roc_auc = None
        avg_precision = None
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Classification report
    report = classification_report(y_test, y_pred, zero_division=0)
    
    # Log to MLflow if active run
    if track_mlflow and mlflow.active_run():
        mlflow.log_metric("test_accuracy", accuracy)
        mlflow.log_metric("test_precision", precision)
        mlflow.log_metric("test_recall", recall)
        mlflow.log_metric("test_f1", f1)
        
        if roc_auc is not None:
            mlflow.log_metric("test_roc_auc", roc_auc)
        if avg_precision is not None:
            mlflow.log_metric("test_avg_precision", avg_precision)
        
        # Log confusion matrix as text
        cm_text = np.array2string(cm)
        mlflow.log_text(cm_text, "confusion_matrix.txt")
        
        # Log classification report
        mlflow.log_text(report, "classification_report.txt")
    
    return Metrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        average_precision=avg_precision,
        confusion_matrix=cm,
        classification_report=report,
    )


def evaluate_binary(y_true, y_prob, threshold: float = 0.5) -> Metrics:
    """Evaluate binary classification predictions.
    
    Legacy function for backward compatibility.
    Use evaluate_model() for more comprehensive evaluation.
    """
    y_true_arr = np.asarray(y_true)
    y_prob_arr = np.asarray(y_prob)
    y_pred = (y_prob_arr >= threshold).astype(int)

    acc = float(accuracy_score(y_true_arr, y_pred))
    precision = float(precision_score(y_true_arr, y_pred, zero_division=0))
    recall = float(recall_score(y_true_arr, y_pred, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred, zero_division=0))
    
    try:
        auc = float(roc_auc_score(y_true_arr, y_prob_arr))
        avg_prec = float(average_precision_score(y_true_arr, y_prob_arr))
    except Exception:
        auc = None
        avg_prec = None
    
    cm = confusion_matrix(y_true_arr, y_pred)
    report = classification_report(y_true_arr, y_pred, zero_division=0)

    return Metrics(
        accuracy=acc,
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=auc,
        average_precision=avg_prec,
        confusion_matrix=cm,
        classification_report=report,
    )


def compare_models(
    models: Dict[str, Pipeline],
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> pd.DataFrame:
    """Compare multiple models on the same test set.
    
    Args:
        models: Dictionary mapping model names to trained pipelines
        x_test: Test features
        y_test: Test labels
        
    Returns:
        DataFrame with comparison metrics for all models
    """
    results = []
    
    for model_name, pipeline in models.items():
        try:
            metrics = evaluate_model(
                pipeline=pipeline,
                x_test=x_test,
                y_test=y_test,
                track_mlflow=False,  # Don't log during comparison
            )
            
            results.append({
                "model": model_name,
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "roc_auc": metrics.roc_auc,
                "avg_precision": metrics.average_precision,
            })
        except Exception as e:
            print(f"Error evaluating {model_name}: {e}")
    
    df = pd.DataFrame(results)
    
    # Sort by F1 score
    if "f1" in df.columns:
        df = df.sort_values("f1", ascending=False)
    
    return df


def print_evaluation_report(metrics: Metrics, model_name: str = "Model"):
    """Print a formatted evaluation report.
    
    Args:
        metrics: Metrics object
        model_name: Name of the model being evaluated
    """
    print("=" * 80)
    print(f"{model_name} Evaluation Report")
    print("=" * 80)
    
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:  {metrics.accuracy:.4f}")
    print(f"  Precision: {metrics.precision:.4f}")
    print(f"  Recall:    {metrics.recall:.4f}")
    print(f"  F1 Score:  {metrics.f1:.4f}")
    
    if metrics.roc_auc is not None:
        print(f"  ROC AUC:   {metrics.roc_auc:.4f}")
    if metrics.average_precision is not None:
        print(f"  Avg Precision: {metrics.average_precision:.4f}")
    
    print(f"\nConfusion Matrix:")
    print(metrics.confusion_matrix)
    
    print(f"\nClassification Report:")
    print(metrics.classification_report)
    
    print("=" * 80)
