from django.shortcuts import render

from utils.power_estimation import estimate_mean_power

from . import ml
from .forms import KM_PER_MI, RideForm

FEATURE_LABELS = {
    "male": "gender",
    "age": "age",
    "height": "height",
    "weight": "weight",
    "mean_hr": "average heart rate",
    "mean_power_per_kg": "power per kg",
}


def index(request):
    form = RideForm(request.POST or None)
    result = None
    try:
        model, model_error = ml.load_model(), None
    except ml.ModelError as exc:
        model, model_error = None, str(exc)

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        power = estimate_mean_power(
            distance_km=d["distance_km"],
            duration_min=d["duration"],
            ascent_m=d["ascent_m"],
            rider_weight_kg=d["weight_kg"],
            bike_weight_kg=d["bike_weight_kg"],
            crr=float(d["surface"]),
            cda=float(d["position"]),
        )
        features = {
            "male": 1 if d["gender"] == "M" else 0,
            "age": d["age"],
            "height": d["height_cm"] / 100,
            "weight": d["weight_kg"],
            "mean_hr": d["mean_hr"],
            "mean_power_per_kg": power / d["weight_kg"],
        }
        speed = d["distance_km"] / (d["duration"] / 60)
        imperial = d["units"] == "imperial"
        result = {
            "power": round(power),
            "power_per_kg": round(features["mean_power_per_kg"], 2),
            "speed": round(speed / KM_PER_MI if imperial else speed, 1),
            "speed_unit": "mph" if imperial else "km/h",
        }
        if model:
            result["vo2max"] = round(ml.predict(model, features), 1)
            result["mae"] = model.get("mae")
            result["outside"] = [FEATURE_LABELS[f] for f in ml.out_of_range(model, features)]

    return render(request, "predictor/index.html", {
        "form": form,
        "units": form.selected_units,
        "result": result,
        "model_error": model_error,
    })
