from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow_experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "mediwatch")
    artifact_dir: str = os.getenv("MEDIWATCH_ARTIFACT_DIR", "artifacts")

    model_path: str = os.getenv("MEDIWATCH_MODEL_PATH", "artifacts/model.joblib")
    preprocessor_path: str = os.getenv(
        "MEDIWATCH_PREPROCESSOR_PATH", "artifacts/preprocessor.joblib"
    )


def get_settings() -> Settings:
    return Settings()
