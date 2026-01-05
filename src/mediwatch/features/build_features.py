from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FeatureSpec:
    target_column: str


def split_features_target(df: pd.DataFrame, spec: FeatureSpec) -> tuple[pd.DataFrame, pd.Series]:
    if spec.target_column not in df.columns:
        raise ValueError(f"Target column not found: {spec.target_column}")
    x = df.drop(columns=[spec.target_column])
    y = df[spec.target_column]
    return x, y
