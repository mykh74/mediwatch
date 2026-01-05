# MediWatch Deployment Guide

## ✅ Model Training Complete!

Your model has been successfully trained and is ready for deployment.

### Training Results

**Best Model**: Gradient Boosting  
**Performance Metrics**:
- F1 Score: 0.5292
- Accuracy: 0.5810
- ROC-AUC: 0.6700

All models saved in: `./models/`

---

## 🚀 Deploying the API

### Step 1: Start the API Server

Open a terminal and run:

```bash
cd /Users/michaelkuzmyn/projects/ik/MediWatch
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ Model loaded from models/Gradient_Boosting.pkl
✓ Preprocessing artifacts loaded
✓ API ready to serve predictions
```

### Step 2: Test the API

**Open a NEW terminal** and test:

```bash
# Activate environment
cd /Users/michaelkuzmyn/projects/ik/MediWatch
source .venv/bin/activate

# Test health endpoint
curl http://localhost:8000/health

# Test model info
curl http://localhost:8000/model/info

# View interactive API documentation
open http://localhost:8000/docs
```

---

## 📡 API Endpoints

### 1. Health Check
```bash
GET http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "1.0.0",
  "timestamp": "2026-01-04T23:44:18"
}
```

### 2. Model Information
```bash
GET http://localhost:8000/model/info
```

**Response**:
```json
{
  "model_name": "Gradient Boosting",
  "model_version": "1.0.0",
  "framework": "scikit-learn",
  "metrics": {
    "f1_score": 0.5292,
    "accuracy": 0.5810,
    "roc_auc": 0.6700
  },
  "features_expected": 24
}
```

### 3. Make a Prediction
```bash
POST http://localhost:8000/predict
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "time_in_hospital": 3,
    "num_lab_procedures": 41,
    "num_procedures": 0,
    "num_medications": 10,
    "number_outpatient": 0,
    "number_emergency": 0,
    "number_inpatient": 0,
    "number_diagnoses": 9,
    "age_[0-10)": 0,
    "age_[10-20)": 0,
    "age_[20-30)": 0,
    "age_[30-40)": 0,
    "age_[40-50)": 0,
    "age_[50-60)": 1,
    "age_[60-70)": 0,
    "age_[70-80)": 0,
    "age_[80-90)": 0,
    "age_[90-100)": 0,
    "gender_Female": 0,
    "gender_Male": 1,
    "diabetesMed_Yes": 1,
    "change_Ch": 0,
    "change_No": 1,
    "has_emergency": 0
  }'
```

**Response**:
```json
{
  "prediction": 1,
  "probability": 0.65,
  "risk_level": "Medium",
  "model_version": "1.0.0"
}
```

**Risk Levels**:
- **Low**: probability < 0.3
- **Medium**: probability 0.3-0.7  
- **High**: probability > 0.7

### 4. Batch Predictions
```bash
POST http://localhost:8000/api/v1/predict/batch
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "patients": [
      {...patient1_features...},
      {...patient2_features...}
    ]
  }'
```

**Response**:
```json
{
  "predictions": [
    {"prediction": 1, "probability": 0.65, "risk_level": "Medium"},
    {"prediction": 0, "probability": 0.25, "risk_level": "Low"}
  ],
  "total_processed": 2,
  "model_version": "1.0.0"
}
```

---

## 🌐 Interactive API Documentation

Once the server is running, visit:

**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

These provide:
- Interactive API testing
- Automatic request/response examples
- Schema documentation
- Try-it-out functionality

---

## 🧪 Testing with Sample Data

Create a test file `test_prediction.json`:

```json
{
  "time_in_hospital": 5,
  "num_lab_procedures": 55,
  "num_procedures": 1,
  "num_medications": 15,
  "number_outpatient": 0,
  "number_emergency": 1,
  "number_inpatient": 0,
  "number_diagnoses": 9,
  "age_[0-10)": 0,
  "age_[10-20)": 0,
  "age_[20-30)": 0,
  "age_[30-40)": 0,
  "age_[40-50)": 0,
  "age_[50-60)": 0,
  "age_[60-70)": 1,
  "age_[70-80)": 0,
  "age_[80-90)": 0,
  "age_[90-100)": 0,
  "gender_Female": 1,
  "gender_Male": 0,
  "diabetesMed_Yes": 1,
  "change_Ch": 1,
  "change_No": 0,
  "has_emergency": 1
}
```

Then test:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @test_prediction.json
```

---

## 🐍 Testing with Python

```python
import requests

# API endpoint
url = "http://localhost:8000/predict"

# Sample patient data
patient_data = {
    "time_in_hospital": 3,
    "num_lab_procedures": 41,
    "num_procedures": 0,
    "num_medications": 10,
    "number_outpatient": 0,
    "number_emergency": 0,
    "number_inpatient": 0,
    "number_diagnoses": 9,
    "age_[50-60)": 1,
    "gender_Male": 1,
    "diabetesMed_Yes": 1,
    "change_No": 1,
    "has_emergency": 0,
    # ... (other encoded features)
}

# Make prediction
response = requests.post(url, json=patient_data)
result = response.json()

print(f"Prediction: {result['prediction']}")
print(f"Probability: {result['probability']:.2%}")
print(f"Risk Level: {result['risk_level']}")
```

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn api.main:app --port 8001
```

### Model Not Loading
```bash
# Check model exists
ls -lh models/Gradient_Boosting.pkl

# Check preprocessing artifacts
ls -lh data/processed/preprocessing_artifacts.pkl
```

### Virtual Environment Issues
```bash
# Ensure venv is activated
source .venv/bin/activate

# Verify Python version
python --version  # Should show 3.13.1

# Check joblib installed
pip list | grep joblib
```

---

## 📊 Production Deployment

### Option 1: Docker

```bash
# Build image
docker build -t mediwatch-api -f api/Dockerfile .

# Run container
docker run -p 8000:8000 mediwatch-api
```

### Option 2: Gunicorn (Production)

```bash
pip install gunicorn

gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Option 3: Kubernetes

See `docs/deployment.md` for full Kubernetes deployment guide.

---

## ✅ Deployment Checklist

- [x] Model trained (Gradient Boosting, F1=0.529)
- [x] Model saved to `models/Gradient_Boosting.pkl`
- [x] Preprocessing artifacts saved
- [x] API code updated and simplified
- [x] All dependencies installed
- [ ] **Start API server** (run command above)
- [ ] **Test health endpoint**
- [ ] **Test prediction endpoint**
- [ ] **View interactive docs at /docs**

---

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ Server starts without errors
2. ✅ `/health` returns `"status": "healthy"`
3. ✅ `/model/info` shows model metrics
4. ✅ `/predict` returns predictions with risk levels
5. ✅ Interactive docs accessible at `/docs`

---

## 📚 Next Steps

1. **Test the API** with real patient data
2. **Monitor predictions** for accuracy
3. **Set up monitoring** (optional - Evidently)
4. **Schedule retraining** (optional - Airflow)
5. **Deploy to production** (Docker/Kubernetes)

---

**Your MediWatch API is ready to deploy!** 🚀

Just run the server command and start making predictions!
