"""
MediWatch FastAPI Application

REST API for patient readmission prediction.
"""

import logging
import os
import json
import sys
import joblib
import pickle
from datetime import datetime
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, 'src')

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MediWatch API",
    description="Binary Patient Readmission Prediction API - Predicts early readmission (<30 days)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "models/Gradient_Boosting.pkl")
PREPROCESSING_ARTIFACTS_PATH = os.getenv(
    "PREPROCESSING_ARTIFACTS_PATH",
    "data/processed/preprocessing_artifacts.pkl"
)

# Global model and preprocessing artifacts
model = None
preprocessing_artifacts = None


@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global model, preprocessing_artifacts
    
    try:
        logger.info("Initializing MediWatch API...")
        
        # Load model
        model_path = Path(MODEL_PATH)
        if model_path.exists():
            model = joblib.load(model_path)
            logger.info(f"✓ Model loaded from {model_path}")
        else:
            logger.error(f"Model not found at {model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load preprocessing artifacts
        artifacts_path = Path(PREPROCESSING_ARTIFACTS_PATH)
        if artifacts_path.exists():
            with open(artifacts_path, 'rb') as f:
                preprocessing_artifacts = pickle.load(f)
            logger.info(f"✓ Preprocessing artifacts loaded from {artifacts_path}")
            logger.info(f"  Features expected: {len(preprocessing_artifacts.feature_names)}")
        else:
            logger.warning(f"Preprocessing artifacts not found at {artifacts_path}")
            preprocessing_artifacts = None
        
        logger.info("✓ API ready to serve predictions")
        
    except Exception as e:
        logger.error(f"Failed to load model or artifacts: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        model = None
        preprocessing_artifacts = None


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "MediWatch API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy" if model is not None else "degraded",
        "model_loaded": model is not None,
        "model_version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/model/info")
async def get_model_info():
    """Get model information."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        # Load training results
        with open('models/training_results.json', 'r') as f:
            results = json.load(f)
        
        model_name = Path(MODEL_PATH).stem.replace('_', ' ')
        model_metrics = results.get(Path(MODEL_PATH).stem, {})
        
        return {
            "model_name": model_name,
            "model_version": "1.0.0",
            "model_type": model_name,
            "framework": "scikit-learn",
            "metrics": {
                "f1_score": model_metrics.get("f1_score", 0.0),
                "accuracy": model_metrics.get("accuracy", 0.0),
                "roc_auc": model_metrics.get("roc_auc", 0.0),
            },
            "features_expected": 24
        }
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model information: {str(e)}"
        )


@app.post("/predict")
def predict_simple(request: dict):
    """Simple prediction endpoint."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        # Convert request to DataFrame
        features_df = pd.DataFrame([request])
        
        # Make prediction (binary classification)
        prediction = model.predict(features_df)[0]
        probability = model.predict_proba(features_df)[0]
        
        # Get probability of positive class (early readmission <30 days)
        readmission_prob = float(probability[1]) if len(probability) > 1 else float(probability[0])
        
        # Get risk level based on readmission probability
        if readmission_prob < 0.3:
            risk_level = "Low"
        elif readmission_prob < 0.7:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        return {
            "prediction": int(prediction),
            "prediction_label": "Early readmission (<30 days)" if prediction == 1 else "No early readmission",
            "readmission_probability": readmission_prob,
            "risk_level": risk_level,
            "model_version": "2.0.0"
        }
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/api/v1/predict")
async def predict_v1(request: dict):
    """Predict patient readmission (v1)."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        # Extract features
        features = request.get('features', request)
        features_df = pd.DataFrame([features])
        
        # Make prediction (binary classification)
        prediction = model.predict(features_df)[0]
        probability = model.predict_proba(features_df)[0]
        
        # Get probability of positive class (early readmission <30 days)
        readmission_prob = float(probability[1]) if len(probability) > 1 else float(probability[0])
        
        # Get risk level based on readmission probability
        if readmission_prob < 0.3:
            risk_level = "Low"
        elif readmission_prob < 0.7:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        return {
            "prediction": int(prediction),
            "prediction_label": "Early readmission (<30 days)" if prediction == 1 else "No early readmission",
            "readmission_probability": readmission_prob,
            "risk_level": risk_level,
            "model_version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/v1/predict/batch")
async def predict_batch_v1(request: dict):
    """Batch prediction endpoint."""
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    patients = request.get('patients', [])
    
    if len(patients) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 patients per batch"
        )
    
    try:
        predictions = []
        
        for patient in patients:
            features_df = pd.DataFrame([patient])
            prediction = model.predict(features_df)[0]
            probability = model.predict_proba(features_df)[0]
            
            # Get probability of positive class (early readmission <30 days)
            readmission_prob = float(probability[1]) if len(probability) > 1 else float(probability[0])
            
            if readmission_prob < 0.3:
                risk_level = "Low"
            elif readmission_prob < 0.7:
                risk_level = "Medium"
            else:
                risk_level = "High"
            
            predictions.append({
                "prediction": int(prediction),
                "prediction_label": "Early readmission (<30 days)" if prediction == 1 else "No early readmission",
                "readmission_probability": readmission_prob,
                "risk_level": risk_level
            })
        
        return {
            "predictions": predictions,
            "total_processed": len(predictions),
            "model_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
