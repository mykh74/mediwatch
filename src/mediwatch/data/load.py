from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a CSV dataset.

    NOTE: This is intentionally minimal; adapt to the Kaggle diabetes dataset schema.
    """
    return pd.read_csv(Path(path))
