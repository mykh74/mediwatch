from __future__ import annotations

from dataclasses import dataclass

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass(frozen=True)
class TrainArtifacts:
    pipeline: Pipeline


def train_baseline(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    preprocessor: ColumnTransformer | None = None,
) -> TrainArtifacts:
    """Train a baseline model.

    This is a minimal stub. Replace with your real preprocessing and model.
    """
    if preprocessor is None:
        preprocessor = ColumnTransformer([], remainder="passthrough")

    clf = LogisticRegression(max_iter=500)
    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", clf)])
    pipeline.fit(x_train, y_train)
    return TrainArtifacts(pipeline=pipeline)


def save_pipeline(pipeline: Pipeline, path: str) -> None:
    joblib.dump(pipeline, path)
