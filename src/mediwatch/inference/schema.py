"""
Request and response schemas for the MediWatch inference API.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class GenderEnum(str, Enum):
    """Gender enumeration."""
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown/Invalid"


class RaceEnum(str, Enum):
    """Race enumeration."""
    CAUCASIAN = "Caucasian"
    AFRICAN_AMERICAN = "AfricanAmerican"
    HISPANIC = "Hispanic"
    ASIAN = "Asian"
    OTHER = "Other"


class MedicationChange(str, Enum):
    """Medication change enumeration."""
    NO = "No"
    CH = "Ch"


class Diabetic(str, Enum):
    """Diabetic medication enumeration."""
    NO = "No"
    YES = "Yes"


class PatientFeatures(BaseModel):
    """
    Patient features for readmission prediction.
    """
    
    # Demographics
    race: Optional[str] = Field(None, description="Patient race")
    gender: Optional[str] = Field(None, description="Patient gender")
    age: Optional[str] = Field(None, description="Age bracket (e.g., '[70-80)')")
    
    # Admission info
    admission_type_id: Optional[int] = Field(None, description="Admission type ID")
    discharge_disposition_id: Optional[int] = Field(None, description="Discharge disposition ID")
    admission_source_id: Optional[int] = Field(None, description="Admission source ID")
    
    # Hospital stay
    time_in_hospital: int = Field(..., ge=1, le=14, description="Days in hospital (1-14)")
    num_lab_procedures: int = Field(..., ge=0, description="Number of lab procedures")
    num_procedures: int = Field(..., ge=0, description="Number of procedures")
    num_medications: int = Field(..., ge=0, description="Number of medications")
    number_outpatient: int = Field(..., ge=0, description="Outpatient visits")
    number_emergency: int = Field(..., ge=0, description="Emergency visits")
    number_inpatient: int = Field(..., ge=0, description="Inpatient visits")
    
    # Diagnoses
    diag_1: Optional[str] = Field(None, description="Primary diagnosis")
    diag_2: Optional[str] = Field(None, description="Secondary diagnosis")
    diag_3: Optional[str] = Field(None, description="Additional diagnosis")
    number_diagnoses: int = Field(..., ge=1, description="Number of diagnoses")
    
    # Test results
    max_glu_serum: Optional[str] = Field(None, description="Max glucose serum result")
    A1Cresult: Optional[str] = Field(None, description="A1C test result")
    
    # Medications (23 diabetes medications)
    metformin: Optional[str] = Field("No", description="Metformin")
    repaglinide: Optional[str] = Field("No", description="Repaglinide")
    nateglinide: Optional[str] = Field("No", description="Nateglinide")
    chlorpropamide: Optional[str] = Field("No", description="Chlorpropamide")
    glimepiride: Optional[str] = Field("No", description="Glimepiride")
    acetohexamide: Optional[str] = Field("No", description="Acetohexamide")
    glipizide: Optional[str] = Field("No", description="Glipizide")
    glyburide: Optional[str] = Field("No", description="Glyburide")
    tolbutamide: Optional[str] = Field("No", description="Tolbutamide")
    pioglitazone: Optional[str] = Field("No", description="Pioglitazone")
    rosiglitazone: Optional[str] = Field("No", description="Rosiglitazone")
    acarbose: Optional[str] = Field("No", description="Acarbose")
    miglitol: Optional[str] = Field("No", description="Miglitol")
    troglitazone: Optional[str] = Field("No", description="Troglitazone")
    tolazamide: Optional[str] = Field("No", description="Tolazamide")
    examide: Optional[str] = Field("No", description="Examide")
    citoglipton: Optional[str] = Field("No", description="Citoglipton")
    insulin: Optional[str] = Field("No", description="Insulin")
    glyburide_metformin: Optional[str] = Field("No", description="Glyburide-metformin")
    glipizide_metformin: Optional[str] = Field("No", description="Glipizide-metformin")
    glimepiride_pioglitazone: Optional[str] = Field("No", description="Glimepiride-pioglitazone")
    metformin_rosiglitazone: Optional[str] = Field("No", description="Metformin-rosiglitazone")
    metformin_pioglitazone: Optional[str] = Field("No", description="Metformin-pioglitazone")
    
    # Change indicators
    change: Optional[str] = Field(None, description="Medication change")
    diabetesMed: Optional[str] = Field(None, description="Diabetic medication prescribed")
    
    class Config:
        schema_extra = {
            "example": {
                "race": "Caucasian",
                "gender": "Female",
                "age": "[50-60)",
                "admission_type_id": 1,
                "discharge_disposition_id": 1,
                "admission_source_id": 7,
                "time_in_hospital": 3,
                "num_lab_procedures": 41,
                "num_procedures": 0,
                "num_medications": 10,
                "number_outpatient": 0,
                "number_emergency": 0,
                "number_inpatient": 0,
                "diag_1": "250.83",
                "diag_2": "250",
                "diag_3": "255",
                "number_diagnoses": 9,
                "max_glu_serum": "None",
                "A1Cresult": "None",
                "metformin": "No",
                "insulin": "Steady",
                "change": "No",
                "diabetesMed": "Yes"
            }
        }


class PredictionRequest(BaseModel):
    """Request model for single prediction."""
    features: PatientFeatures = Field(..., description="Patient features")


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""
    patients: List[PatientFeatures] = Field(..., min_items=1, max_items=100, description="Patients (max 100)")


class PredictionResponse(BaseModel):
    """Response model for single prediction (Binary Classification)."""
    prediction: int = Field(..., description="Binary prediction: 0=No early readmission, 1=Early readmission (<30 days)")
    prediction_label: str = Field(..., description="Human-readable prediction label")
    readmission_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of early readmission (<30 days)")
    risk_level: str = Field(..., description="Risk level: Low, Medium, High")
    model_version: str = Field(..., description="Model version")
    
    @validator("risk_level")
    def validate_risk_level(cls, v):
        if v not in ["Low", "Medium", "High"]:
            raise ValueError("risk_level must be Low, Medium, or High")
        return v


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""
    predictions: List[PredictionResponse] = Field(..., description="Predictions")
    total_processed: int = Field(..., description="Total processed")
    model_version: str = Field(..., description="Model version")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Model loaded")
    model_version: Optional[str] = Field(None, description="Model version")
    timestamp: str = Field(..., description="Timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error detail")
    timestamp: str = Field(..., description="Error timestamp")


class ModelInfo(BaseModel):
    """Model information response."""
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    model_stage: str = Field(..., description="Model stage")
    framework: str = Field(..., description="ML framework")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")
    features_expected: int = Field(..., description="Expected features")


# Legacy compatibility
class PredictRequest(BaseModel):
    """Legacy prediction request."""
    features: dict


class PredictResponse(BaseModel):
    """Legacy prediction response."""
    label: int
    probability: float
