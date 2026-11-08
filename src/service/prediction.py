from pydantic import BaseModel

class Prediction(BaseModel):
	power_w: float
	power_per_kg: float
	vo2max: float | None = None
	notice: str | None = None