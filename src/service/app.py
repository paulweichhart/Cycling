"""VO2max prediction service.

Takes an Apple Watch ride summary (metric units), estimates the mean power with
utils.power_estimation and applies the trained linear regression.

The model is a joblib dump of (dv, model): a fitted sklearn DictVectorizer and
the regression, written by utils/train_model.py to src/utils/model.bin
(override with VO2MAX_MODEL_PATH).

dv receives the features under the column names of data/cycling_tests.csv
(see FEATURES). It ignores names it was not fit on, so any subset works.
The file is re-read when it changes, so a new export needs no restart.

Run from src/:  uvicorn service.app:app --port 8001 --reload
"""
from __future__ import annotations

import os
from pathlib import Path

import joblib

from fastapi import FastAPI

from utils.power_estimation import estimate_mean_power

from .ride import Ride
from .error import ModelError
from .prediction import Prediction

MODEL_PATH = Path(os.environ.get(
    "VO2MAX_MODEL_PATH", Path(__file__).resolve().parents[1] / "utils" / "model.bin"))

# feature name -> unit, the same as data/cycling_tests.csv
FEATURES = {
    "gender": '"F" or "M"',
    "age": "years",
    "weight": "kg",
    "mean_hr": "bpm",
    "mean_power_per_kg": "W/kg",
}

app = FastAPI(title="CyclingML VO2max service",
              description="Predicts VO2max (mL/kg/min) from a ride summary.")

_cache: dict = {"mtime": None, "model": None}

def load_model():
    """Return (dv, model); re-read model.bin when the file changed."""
    try:
        mtime = MODEL_PATH.stat().st_mtime
    except FileNotFoundError:
        raise ModelError(f"No model yet. Train it with `python -m utils.train_model` (expected {MODEL_PATH})")
    if _cache["mtime"] != mtime:
        _cache.update(mtime=mtime, model=joblib.load(MODEL_PATH))
    return _cache["model"]


@app.get("/health")
def health() -> dict:
    try:
        load_model()
        loaded = True
    except ModelError:
        loaded = False
    return {"status": "ok", "model_loaded": loaded}

@app.post("/predict", response_model=Prediction)
def predict(ride: Ride) -> Prediction:
    power = estimate_mean_power(
        distance_km=ride.distance_km,
        duration_min=ride.duration_min,
        ascent_m=ride.ascent_m,
        rider_weight_kg=ride.weight_kg,
        bike_weight_kg=ride.bike_weight_kg,
        crr=ride.crr,
        cda=ride.cda,
    )
    features = {
        "gender": ride.gender,
        "age": ride.age,
        "weight": ride.weight_kg,
        "mean_hr": ride.mean_hr,
        "mean_power_per_kg": power / ride.weight_kg,
    }
    prediction = Prediction(power_w=round(power, 1), power_per_kg=round(features["mean_power_per_kg"], 3))
    try:
        dv, model = load_model()
        value = model.predict(dv.transform([features]))[0]
        prediction.vo2max = round(float(value), 1)
    except ModelError as exc:
        prediction.notice = str(exc)
    return prediction
