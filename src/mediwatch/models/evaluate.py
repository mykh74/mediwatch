from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score


@dataclass(frozen=True)
class Metrics:
    accuracy: float
    roc_auc: float | None


def evaluate_binary(y_true, y_prob) -> Metrics:
    y_true_arr = np.asarray(y_true)
    y_prob_arr = np.asarray(y_prob)
    y_pred = (y_prob_arr >= 0.5).astype(int)

    acc = float(accuracy_score(y_true_arr, y_pred))
    try:
        auc = float(roc_auc_score(y_true_arr, y_prob_arr))
    except Exception:
        auc = None

    return Metrics(accuracy=acc, roc_auc=auc)
