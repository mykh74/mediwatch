from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SplitData:
    train: pd.DataFrame
    test: pd.DataFrame


def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning placeholder.

    Implement:
    - missing value handling
    - type casting
    - target label normalization
    """
    return df.copy()
