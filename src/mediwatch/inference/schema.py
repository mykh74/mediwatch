from __future__ import annotations

from pydantic import BaseModel


class PredictRequest(BaseModel):
    """Generic prediction request.

    Replace `features` with a typed schema once you lock the dataset feature set.
    """

    features: dict


class PredictResponse(BaseModel):
    label: int
    probability: float
