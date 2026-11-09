import re

from django import forms

INPUT_CLASSES = (
    "block w-full rounded-xl border-0 bg-zinc-100 px-4 py-3 pr-20 text-base text-zinc-900 "
    "placeholder:text-zinc-400 transition focus:bg-white focus:outline-none focus:ring-2 "
    "focus:ring-[#0071e3] dark:bg-zinc-800 dark:text-white dark:placeholder:text-zinc-500 "
    "dark:focus:bg-zinc-900"
)
SELECT_CLASSES = INPUT_CLASSES.replace("pr-20", "pr-10") + " appearance-none"
NARROW_INPUT_CLASSES = INPUT_CLASSES.replace("pr-20", "pr-9")  # feet / inches side by side
SEGMENT_CLASSES = "peer sr-only"

# drag area (m²) and rolling resistance, see power_estimation.py
POSITIONS = [("0.30", "Drops"), ("0.35", "Hoods"), ("0.45", "Upright")]
SURFACES = [("0.004", "Road"), ("0.008", "Gravel")]
UNITS = [("metric", "Metric"), ("imperial", "Imperial")]

KG_PER_LB = 0.45359237
KM_PER_MI = 1.609344
M_PER_FT = 0.3048
CM_PER_IN = 2.54

# form field -> (metric name in cleaned_data, metric per imperial unit, metric unit, imperial unit, metric limits)
CONVERTED = {
    "weight": ("weight_kg", KG_PER_LB, "kg", "lb", (30, 200)),
    "distance": ("distance_km", KM_PER_MI, "km", "mi", (0.5, 500)),
    "ascent": ("ascent_m", M_PER_FT, "m", "ft", (0, 10000)),
    "bike_weight": ("bike_weight_kg", KG_PER_LB, "kg", "lb", (3, 40)),
}
HEIGHT_LIMITS_CM = (120, 230)

DURATION_RE = re.compile(r"^(?:(\d+):)?(\d{1,3}):(\d{2})$")

def number(placeholder, imperial_placeholder=None, classes=INPUT_CLASSES, **attrs):
    """A numeric input; imperial_placeholder is swapped in by the page script when the units change."""
    attrs = {"class": classes, "placeholder": placeholder, "inputmode": "decimal", "step": "any", **attrs}
    if imperial_placeholder:
        attrs["data-placeholder-metric"] = placeholder
        attrs["data-placeholder-imperial"] = imperial_placeholder
    return forms.NumberInput(attrs=attrs)


def _fmt(value: float) -> str:
    return f"{value:.1f}".removesuffix(".0")


class RideForm(forms.Form):
    """Values are entered in the chosen units; clean() returns them in metric
    (height_cm, weight_kg, distance_km, ascent_m, bike_weight_kg)."""

    units = forms.ChoiceField(choices=UNITS, initial="metric",
                              widget=forms.RadioSelect(attrs={"class": SEGMENT_CLASSES}))
    gender = forms.ChoiceField(
        choices=[("F", "Female"), ("M", "Male")],
        widget=forms.RadioSelect(attrs={"class": SEGMENT_CLASSES}),
    )
    age = forms.IntegerField(min_value=10, max_value=100, widget=number("35", inputmode="numeric"))
    height_cm = forms.FloatField(label="Height", required=False, widget=number("178"))
    height_ft = forms.IntegerField(label="Feet", required=False,
                                   widget=number("5", classes=NARROW_INPUT_CLASSES, inputmode="numeric"))
    height_in = forms.FloatField(label="Inches", required=False,
                                 widget=number("10", classes=NARROW_INPUT_CLASSES))
    weight = forms.FloatField(min_value=0, widget=number("72", "160"))

    distance = forms.FloatField(min_value=0, widget=number("40.2", "25"))
    duration = forms.CharField(
        label="Workout time",
        help_text="As shown on the watch, e.g. 1:20:15 or 45:30",
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES, "placeholder": "1:20:15",
                                      "inputmode": "text", "autocomplete": "off"}),
    )
    ascent = forms.FloatField(label="Elevation gain", min_value=0, widget=number("350", "1150"))
    mean_hr = forms.IntegerField(label="Avg. heart rate", min_value=60, max_value=220,
                                 widget=number("145", inputmode="numeric"))

    position = forms.ChoiceField(label="Riding position", choices=POSITIONS, initial="0.30",
                                 widget=forms.Select(attrs={"class": SELECT_CLASSES}))
    surface = forms.ChoiceField(choices=SURFACES, initial="0.004",
                                widget=forms.Select(attrs={"class": SELECT_CLASSES}))
    bike_weight = forms.FloatField(label="Bike weight", min_value=0, initial=9, widget=number("9", "20"))

    def clean_duration(self) -> float:
        """'1:20:15' or '45:30' -> minutes."""
        value = self.cleaned_data["duration"].strip()
        m = DURATION_RE.match(value)
        if not m:
            raise forms.ValidationError("Use h:mm:ss or mm:ss, e.g. 1:20:15.")
        hours, minutes, seconds = int(m.group(1) or 0), int(m.group(2)), int(m.group(3))
        if seconds >= 60 or (m.group(1) and minutes >= 60):
            raise forms.ValidationError("Minutes and seconds must be below 60.")
        total = hours * 60 + minutes + seconds / 60
        if total < 5:
            raise forms.ValidationError("The ride should last at least 5 minutes.")
        return total

    @property
    def selected_units(self) -> str:
        """The units to show, also for an invalid or unbound form."""
        value = self["units"].value()
        return value if value in dict(UNITS) else "metric"

    def clean(self):
        data = super().clean()
        imperial = data.get("units") == "imperial"
        self._clean_height(data, imperial)

        for name, (metric_name, factor, metric_unit, imperial_unit, (low, high)) in CONVERTED.items():
            value = data.get(name)
            if value is None:
                continue
            metric = value * factor if imperial else value
            if not low <= metric <= high:
                unit = imperial_unit if imperial else metric_unit
                scale = 1 / factor if imperial else 1
                self.add_error(name, f"Enter a value between {_fmt(low * scale)} and {_fmt(high * scale)} {unit}.")
                continue
            data[metric_name] = metric

        distance, duration = data.get("distance_km"), data.get("duration")
        if distance and duration:
            speed = distance / (duration / 60)
            if not 3 <= speed <= 60:
                shown = f"{speed / KM_PER_MI:.1f} mph" if imperial else f"{speed:.1f} km/h"
                raise forms.ValidationError(
                    f"An average speed of {shown} looks wrong. Check distance and workout time.")
        return data

    def _clean_height(self, data, imperial: bool) -> None:
        low, high = HEIGHT_LIMITS_CM
        if imperial:
            feet, inches = data.get("height_ft"), data.get("height_in") or 0
            if feet is None:
                self.add_error("height_ft", "Enter your height.")
                return
            if not 0 <= inches < 12:
                self.add_error("height_in", "Inches must be between 0 and 11.")
                return
            cm = (feet * 12 + inches) * CM_PER_IN
            if not low <= cm <= high:
                self.add_error("height_ft", "Enter a height between 3 ft 11 in and 7 ft 6 in.")
                return
        else:
            cm = data.get("height_cm")
            if cm is None:
                self.add_error("height_cm", "Enter your height.")
                return
            if not low <= cm <= high:
                self.add_error("height_cm", f"Enter a height between {low} and {high} cm.")
                return
        data["height_cm"] = cm
