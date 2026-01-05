from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from mediwatch.config import get_settings
from mediwatch.inference.predict import load_pipeline, predict_proba
from mediwatch.inference.schema import PredictRequest, PredictResponse

load_dotenv()

app = FastAPI(title="MediWatch API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    settings = get_settings()

    try:
        pipeline = load_pipeline(settings.model_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model artifact not found. Train/export a model to "
                f"{settings.model_path}"
            ),
        )

    prob = predict_proba(pipeline, req.features)
    label = 1 if prob >= 0.5 else 0
    return PredictResponse(label=label, probability=prob)
