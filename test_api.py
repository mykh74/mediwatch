#!/usr/bin/env python3
"""
Test script for MediWatch API
Tests binary classification endpoints for early readmission prediction.
"""

import requests
import json

API_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("=" * 80)
    print("Testing Health Endpoint")
    print("=" * 80)
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()["model_loaded"] == True
    print("✓ Health check passed\n")


def test_model_info():
    """Test model info endpoint."""
    print("=" * 80)
    print("Testing Model Info Endpoint")
    print("=" * 80)
    
    response = requests.get(f"{API_URL}/model/info")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert "model_name" in response.json()
    print("✓ Model info check passed\n")


def test_single_prediction():
    """Test single prediction endpoint."""
    print("=" * 80)
    print("Testing Single Prediction Endpoint")
    print("=" * 80)
    
    # Sample patient data
    sample_patient = {
        "patient_nbr": 44011827.0,
        "time_in_hospital": 4.0,
        "num_lab_procedures": 40.0,
        "num_procedures": 0.0,
        "num_medications": 17.0,
        "number_outpatient": 0.0,
        "number_emergency": 0.0,
        "number_inpatient": 1.0,
        "number_diagnoses": 9.0,
        "num_diagnoses": 4.0,
        "procedures_per_day": 0.0,
        "meds_per_diagnosis": 3.4,
        "lab_procedures_per_day": 8.0,
        "payer_code_encoded": 7.0,
        "medical_specialty_encoded": 18.0,
        "diag_1_encoded": 405.0,
        "diag_2_encoded": 133.0,
        "diag_3_encoded": 139.0,
        "troglitazone_encoded": 0.0,
        "citoglipton_encoded": 0.0,
        "metformin-rosiglitazone_encoded": 0.0,
        "metformin-pioglitazone_encoded": 0.0,
        "change_encoded": 0.0,
        "diabetesMed_encoded": 1.0
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=sample_patient
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    assert response.status_code == 200
    assert "prediction" in result
    assert "readmission_probability" in result
    assert "risk_level" in result
    assert result["prediction"] in [0, 1]
    assert 0 <= result["readmission_probability"] <= 1
    assert result["risk_level"] in ["Low", "Medium", "High"]
    
    print(f"\n✓ Prediction: {result['prediction_label']}")
    print(f"✓ Readmission Probability: {result['readmission_probability']:.2%}")
    print(f"✓ Risk Level: {result['risk_level']}")
    print("✓ Single prediction passed\n")


def test_batch_prediction():
    """Test batch prediction endpoint."""
    print("=" * 80)
    print("Testing Batch Prediction Endpoint")
    print("=" * 80)
    
    # Two sample patients
    patients = [
        {
            "patient_nbr": 44011827.0,
            "time_in_hospital": 4.0,
            "num_lab_procedures": 40.0,
            "num_procedures": 0.0,
            "num_medications": 17.0,
            "number_outpatient": 0.0,
            "number_emergency": 0.0,
            "number_inpatient": 1.0,
            "number_diagnoses": 9.0,
            "num_diagnoses": 4.0,
            "procedures_per_day": 0.0,
            "meds_per_diagnosis": 3.4,
            "lab_procedures_per_day": 8.0,
            "payer_code_encoded": 7.0,
            "medical_specialty_encoded": 18.0,
            "diag_1_encoded": 405.0,
            "diag_2_encoded": 133.0,
            "diag_3_encoded": 139.0,
            "troglitazone_encoded": 0.0,
            "citoglipton_encoded": 0.0,
            "metformin-rosiglitazone_encoded": 0.0,
            "metformin-pioglitazone_encoded": 0.0,
            "change_encoded": 0.0,
            "diabetesMed_encoded": 1.0
        },
        {
            "patient_nbr": 3509442.0,
            "time_in_hospital": 5.0,
            "num_lab_procedures": 43.0,
            "num_procedures": 3.0,
            "num_medications": 34.0,
            "number_outpatient": 0.0,
            "number_emergency": 0.0,
            "number_inpatient": 1.0,
            "number_diagnoses": 9.0,
            "num_diagnoses": 4.0,
            "procedures_per_day": 0.5,
            "meds_per_diagnosis": 6.8,
            "lab_procedures_per_day": 7.17,
            "payer_code_encoded": 7.0,
            "medical_specialty_encoded": 18.0,
            "diag_1_encoded": 287.0,
            "diag_2_encoded": 646.0,
            "diag_3_encoded": 273.0,
            "troglitazone_encoded": 0.0,
            "citoglipton_encoded": 0.0,
            "metformin-rosiglitazone_encoded": 0.0,
            "metformin-pioglitazone_encoded": 0.0,
            "change_encoded": 1.0,
            "diabetesMed_encoded": 0.0
        }
    ]
    
    response = requests.post(
        f"{API_URL}/api/v1/predict/batch",
        json={"patients": patients}
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Predictions: {json.dumps(result, indent=2)}")
    
    assert response.status_code == 200
    assert "predictions" in result
    assert result["total_processed"] == 2
    assert len(result["predictions"]) == 2
    
    for i, pred in enumerate(result["predictions"]):
        print(f"\nPatient {i+1}:")
        print(f"  Prediction: {pred['prediction_label']}")
        print(f"  Probability: {pred['readmission_probability']:.2%}")
        print(f"  Risk: {pred['risk_level']}")
    
    print("\n✓ Batch prediction passed\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("MediWatch API Test Suite - Binary Classification")
    print("=" * 80 + "\n")
    
    try:
        test_health()
        test_model_info()
        test_single_prediction()
        test_batch_prediction()
        
        print("=" * 80)
        print("✓ ALL TESTS PASSED!")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
