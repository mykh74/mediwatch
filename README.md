# MediWatch

Predicting patient readmission through Machine Learning + MLOps.

## What’s in this repo
- `notebooks/`: experimentation notebook(s) (EDA, feature engineering, model exploration)
- `src/mediwatch/`: reusable Python package (data, features, training, tuning, registry)
- `api/`: REST inference API (FastAPI) that loads the exported model + transformers
- `orchestration/`: Airflow DAG stub + notes for orchestrating pipelines
- `monitoring/`: Evidently-based drift report stub

## Quickstart (local, minimal)
1. Create an environment and install deps:
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Run the API (stub):
   - `uvicorn api.main:app --reload --port 8000`
3. Open API docs:
   - `http://127.0.0.1:8000/docs`

## Configuration
Copy `.env.example` to `.env` and set values as needed.

## Next steps
- Implement data ingestion + preprocessing in `src/mediwatch/data/`
- Implement training + MLflow logging in `src/mediwatch/models/` and `src/mediwatch/registry/`
- Export model artifacts into `artifacts/` and wire the API to load them
- Add an Airflow DAG that runs training → deployment → monitoring → retraining
