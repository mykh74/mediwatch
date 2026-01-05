from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline


def load_pipeline(path: str | Path) -> Pipeline:
    return joblib.load(Path(path))


def predict_proba(pipeline: Pipeline, features: dict) -> float:
    df = pd.DataFrame([features])
    proba = pipeline.predict_proba(df)[:, 1]
    return float(proba[0])
