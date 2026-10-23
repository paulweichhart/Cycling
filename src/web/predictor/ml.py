"""Load the exported linear regression and apply it to the form's values.

The model is the file model.json next to this module. Export it from your own
training code in this format (only "intercept" and "coefficients" are required):

    {
      "intercept": -10.5,
      "coefficients": {"male": 2.1, "mean_power_per_kg": 17.0, ...},
      "mae": 3.7,                                  # optional: shown as ± on the page
      "ranges": {"mean_power_per_kg": [1.9, 4.2]}  # optional: warn outside these
    }

    prediction = intercept + sum(coefficient * feature)

The coefficients may use any of the FEATURES below, in the units given there
(the same units as data/cycling_tests.csv). The file is read on every request,
so a newly exported model shows up without restarting the server.
"""
from __future__ import annotations

import json
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "model.json"

# feature name -> description; the units match data/cycling_tests.csv
FEATURES = {
    "male": "1 for male, 0 for female",
    "age": "years",
    "height": "m",
    "weight": "kg",
    "mean_hr": "mean heart rate of the ride, bpm",
    "mean_power_per_kg": "estimated mean power, W/kg",
}


class ModelError(Exception):
    """model.json is missing or not in the expected format."""


def load_model(path: Path = MODEL_PATH) -> dict:
    if not path.exists():
        raise ModelError(f"No model yet. Export your trained regression to {path.name} "
                         f"in web/predictor/ to see a VO2max estimate.")
    try:
        model = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ModelError(f"{path.name} is not valid JSON: {exc}") from exc

    if not isinstance(model.get("intercept"), (int, float)):
        raise ModelError(f'{path.name} needs a numeric "intercept".')
    coefficients = model.get("coefficients")
    if not isinstance(coefficients, dict) or not coefficients:
        raise ModelError(f'{path.name} needs "coefficients" as {{feature: number}}.')
    unknown = set(coefficients) - set(FEATURES)
    if unknown:
        raise ModelError(f"Unknown features in {path.name}: {', '.join(sorted(unknown))}. "
                         f"Available: {', '.join(FEATURES)}.")
    if not all(isinstance(v, (int, float)) for v in coefficients.values()):
        raise ModelError(f"All coefficients in {path.name} must be numbers.")
    return model


def predict(model: dict, features: dict[str, float]) -> float:
    return model["intercept"] + sum(c * features[name] for name, c in model["coefficients"].items())


def out_of_range(model: dict, features: dict[str, float]) -> list[str]:
    ranges = model.get("ranges") or {}
    outside = []
    for name in model["coefficients"]:
        bounds = ranges.get(name)
        if bounds and not bounds[0] <= features[name] <= bounds[1]:
            outside.append(name)
    return outside
