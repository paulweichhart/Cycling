import json
import urllib.error
import urllib.request

from django.conf import settings
from django.shortcuts import render

from .forms import KM_PER_MI, RideForm


class ServiceError(Exception):
    """The prediction service could not be reached or returned an error."""


def call_service(payload: dict) -> dict:
    url = settings.VO2MAX_SERVICE_URL.rstrip("/") + "/predict"
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=settings.VO2MAX_SERVICE_TIMEOUT) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ServiceError(f"The prediction service rejected the ride ({exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise ServiceError(f"The prediction service is not reachable at {url}.") from exc


def index(request):
    form = RideForm(request.POST or None)
    result = None
    model_error = None

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        payload = {
            "gender": d["gender"],
            "age": d["age"],
            "weight_kg": d["weight_kg"],
            "mean_hr": d["mean_hr"],
            "distance_km": d["distance_km"],
            "duration_min": d["duration"],
            "ascent_m": d["ascent_m"],
            "bike_weight_kg": d["bike_weight_kg"],
            "crr": float(d["surface"]),
            "cda": float(d["position"]),
        }
        try:
            prediction = call_service(payload)
        except ServiceError as exc:
            model_error = str(exc)
        else:
            speed = d["distance_km"] / (d["duration"] / 60)
            imperial = d["units"] == "imperial"
            result = {
                "power": round(prediction["power_w"]),
                "power_per_kg": round(prediction["power_per_kg"], 2),
                "speed": round(speed / KM_PER_MI if imperial else speed, 1),
                "speed_unit": "mph" if imperial else "km/h",
                "vo2max": prediction.get("vo2max"),
            }
            model_error = prediction.get("notice")

    return render(request, "predictor/index.html", {
        "form": form,
        "units": form.selected_units,
        "result": result,
        "model_error": model_error,
    })
