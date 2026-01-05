"""
Inference module for patient readmission prediction.

Handles model loading, preprocessing, and prediction generation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
import mlflow
from sklearn.pipeline import Pipeline

from mediwatch.data.preprocess import PreprocessingArtifacts, apply_preprocessing
from mediwatch.inference.schema import PatientFeatures, PredictionResponse

logger = logging.getLogger(__name__)


class ModelPredictor:
    """
    Predictor class for loading models and making predictions.
    """
    
    def __init__(
        self,
        model_uri: Optional[str] = None,
        model_path: Optional[Path] = None,
        preprocessing_artifacts_path: Optional[Path] = None,
        mlflow_tracking_uri: str = "http://127.0.0.1:5000"
    ):
        """
        Initialize the predictor.
        
        Args:
            model_uri: MLflow model URI (e.g., "models:/model_name/Production")
            model_path: Local path to model file (alternative to model_uri)
            preprocessing_artifacts_path: Path to preprocessing artifacts
            mlflow_tracking_uri: MLflow tracking server URI
        """
        self.model_uri = model_uri
        self.model_path = model_path
        self.preprocessing_artifacts_path = preprocessing_artifacts_path
        self.mlflow_tracking_uri = mlflow_tracking_uri
        
        self.model: Optional[Pipeline] = None
        self.preprocessing_artifacts: Optional[PreprocessingArtifacts] = None
        self.model_version: Optional[str] = None
        
        # Risk thresholds
        self.low_risk_threshold = 0.3
        self.high_risk_threshold = 0.7
    
    def load_model(self) -> None:
        """Load model from MLflow or local path."""
        try:
            if self.model_uri:
                # Load from MLflow
                mlflow.set_tracking_uri(self.mlflow_tracking_uri)
                logger.info(f"Loading model from MLflow: {self.model_uri}")
                self.model = mlflow.pyfunc.load_model(self.model_uri)
                self.model_version = self.model_uri.split("/")[-1]
                logger.info(f"Model loaded successfully: version {self.model_version}")
                
            elif self.model_path:
                # Load from local path
                logger.info(f"Loading model from local path: {self.model_path}")
                import joblib
                self.model = joblib.load(self.model_path)
                self.model_version = "local"
                logger.info("Model loaded successfully from local path")
                
            else:
                raise ValueError("Either model_uri or model_path must be provided")
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def load_preprocessing_artifacts(self) -> None:
        """Load preprocessing artifacts."""
        if not self.preprocessing_artifacts_path:
            logger.warning("No preprocessing artifacts path provided")
            return
        
        try:
            logger.info(f"Loading preprocessing artifacts from {self.preprocessing_artifacts_path}")
            self.preprocessing_artifacts = PreprocessingArtifacts.load(
                self.preprocessing_artifacts_path
            )
            logger.info("Preprocessing artifacts loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load preprocessing artifacts: {e}")
            raise
    
    def preprocess_features(self, features: Union[Dict, PatientFeatures, pd.DataFrame]) -> pd.DataFrame:
        """
        Preprocess input features.
        
        Args:
            features: Raw features as dict, PatientFeatures, or DataFrame
            
        Returns:
            Preprocessed features as DataFrame
        """
        # Convert to DataFrame
        if isinstance(features, dict):
            df = pd.DataFrame([features])
        elif isinstance(features, PatientFeatures):
            df = pd.DataFrame([features.dict()])
        elif isinstance(features, pd.DataFrame):
            df = features.copy()
        else:
            raise ValueError(f"Unsupported features type: {type(features)}")
        
        # Apply preprocessing if artifacts available
        if self.preprocessing_artifacts:
            try:
                df = apply_preprocessing(df, self.preprocessing_artifacts)
            except Exception as e:
                logger.warning(f"Preprocessing failed, using raw features: {e}")
        
        return df
    
    def predict_single(self, features: Union[Dict, PatientFeatures]) -> PredictionResponse:
        """
        Make prediction for a single patient.
        
        Args:
            features: Patient features
            
        Returns:
            PredictionResponse with prediction, probability, and risk level
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Preprocess
        df = self.preprocess_features(features)
        
        # Make prediction
        try:
            prediction = int(self.model.predict(df)[0])
            probability = float(self.model.predict_proba(df)[0, 1])
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
        
        # Determine risk level
        risk_level = self._get_risk_level(probability)
        
        return PredictionResponse(
            prediction=prediction,
            probability=probability,
            risk_level=risk_level,
            model_version=self.model_version or "unknown"
        )
    
    def predict_batch(
        self,
        features_list: List[Union[Dict, PatientFeatures]]
    ) -> List[PredictionResponse]:
        """
        Make predictions for multiple patients.
        
        Args:
            features_list: List of patient features
            
        Returns:
            List of PredictionResponse objects
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        predictions = []
        
        for features in features_list:
            try:
                pred = self.predict_single(features)
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Failed to predict for patient: {e}")
                # Add error prediction
                predictions.append(
                    PredictionResponse(
                        prediction=-1,
                        probability=0.0,
                        risk_level="Unknown",
                        model_version=self.model_version or "unknown"
                    )
                )
        
        return predictions
    
    def _get_risk_level(self, probability: float) -> str:
        """
        Determine risk level based on probability.
        
        Args:
            probability: Readmission probability (0-1)
            
        Returns:
            Risk level: "Low", "Medium", or "High"
        """
        if probability < self.low_risk_threshold:
            return "Low"
        elif probability < self.high_risk_threshold:
            return "Medium"
        else:
            return "High"
    
    def get_model_info(self) -> Dict:
        """Get model information."""
        return {
            "model_loaded": self.model is not None,
            "model_version": self.model_version,
            "model_uri": self.model_uri,
            "preprocessing_loaded": self.preprocessing_artifacts is not None,
            "mlflow_tracking_uri": self.mlflow_tracking_uri
        }


# Legacy functions for backward compatibility
def load_pipeline(path: str | Path) -> Pipeline:
    """Load model pipeline from path."""
    import joblib
    return joblib.load(Path(path))


def predict_proba(pipeline: Pipeline, features: dict) -> float:
    """Get prediction probability."""
    df = pd.DataFrame([features])
    proba = pipeline.predict_proba(df)[:, 1]
    return float(proba[0])


# Convenience function for quick predictions
def predict(
    features: Union[Dict, PatientFeatures],
    model_name: str = "mediwatch_readmission_classifier",
    stage: str = "Production",
    mlflow_tracking_uri: str = "http://127.0.0.1:5000"
) -> PredictionResponse:
    """
    Make a quick prediction using a registered MLflow model.
    
    Args:
        features: Patient features
        model_name: MLflow model name
        stage: Model stage (Production, Staging, None)
        mlflow_tracking_uri: MLflow tracking URI
        
    Returns:
        PredictionResponse
    """
    model_uri = f"models:/{model_name}/{stage}"
    
    predictor = ModelPredictor(
        model_uri=model_uri,
        mlflow_tracking_uri=mlflow_tracking_uri
    )
    predictor.load_model()
    
    return predictor.predict_single(features)
