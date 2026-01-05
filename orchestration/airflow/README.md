# Airflow orchestration (stub)

This folder is a placeholder for orchestrating the end-to-end workflow:
- data prep
- training + HPO
- model selection and packaging
- deployment
- monitoring + drift checks
- retraining triggers

## Notes
- If you use Docker Compose for Airflow, mount host directories that contain:
  - datasets (`data/`)
  - code (`src/`, `api/`)
  - artifacts (`artifacts/`)
- Ensure MLflow/Jenkins endpoints are reachable from containers.

## DAG
See `dags/mediwatch_pipeline.py` for the pipeline skeleton.
