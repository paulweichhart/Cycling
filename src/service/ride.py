from pydantic import BaseModel, Field
from typing import Literal

class Ride(BaseModel):
	gender: Literal["F", "M"]
	age: float = Field(ge=10, le=100, description="years")
	weight_kg: float = Field(ge=30, le=200)
	mean_hr: float = Field(ge=60, le=220, description="average heart rate, bpm")
	distance_km: float = Field(ge=0.5, le=500)
	duration_min: float = Field(ge=5, description="workout time in minutes")
	ascent_m: float = Field(ge=0, le=10000, description="elevation gain")
	bike_weight_kg: float = Field(9.0, ge=3, le=40)
	crr: float = Field(0.004, gt=0, lt=0.05, description="rolling resistance: 0.004 road, 0.008 gravel")
	cda: float = Field(0.30, gt=0, lt=1, description="drag area m²: 0.30 drops, 0.35 hoods, 0.45 upright")