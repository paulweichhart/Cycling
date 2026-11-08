"""Estimate the mean cycling power of a ride from its summary values.

Physics model: the rider's power overcomes climbing, rolling resistance and
air drag, divided by the drivetrain efficiency:

    P = (P_climb + P_roll + P_air) / efficiency

    P_climb = m * g * ascent / duration      (work against gravity, spread over the ride)
    P_roll  = crr * m * g * v
    P_air   = 0.5 * rho * cda * v**3

with m = rider + bike and v = distance / duration (the average speed).

Limits: wind and drafting are unknown, so flat rides are the least accurate.
P_air uses the average speed, which underestimates air drag for rides with
changing speed. Descents are assumed to return nothing (coasting), which is
right for a climb test and roughly right for a hilly ride.
"""
from __future__ import annotations

G = 9.81  # m/s²

def estimate_mean_power(
    distance_km: float,
    duration_min: float,
    ascent_m: float,
    rider_weight_kg: float,
    bike_weight_kg: float = 9.0,
    crr: float = 0.004,
    cda: float = 0.35,
    air_density: float = 1.2,
    efficiency: float = 0.97,
) -> float:
    """Mean power in watts from a ride summary.

    distance_km, duration_min, ascent_m: from the workout summary (moving time
    is better than total time when the ride had stops).
    crr: rolling resistance, 0.004 for road tyres on asphalt, ~0.008 for gravel.
    cda: drag area in m², ~0.3 on the drops, ~0.35 on the hoods, ~0.45 upright.
    air_density: 1.2 kg/m³ near sea level at ~20 °C; lower at altitude.
    """
    if distance_km <= 0 or duration_min <= 0 or rider_weight_kg <= 0:
        raise ValueError("distance, duration and weight must be positive")
    if ascent_m < 0:
        raise ValueError("ascent cannot be negative")

    seconds = duration_min * 60
    speed = distance_km * 1000 / seconds  # m/s
    mass = rider_weight_kg + bike_weight_kg

    p_climb = mass * G * ascent_m / seconds
    p_roll = crr * mass * G * speed
    p_air = 0.5 * air_density * cda * speed ** 3
    return (p_climb + p_roll + p_air) / efficiency


def estimate_mean_power_per_kg(distance_km: float, duration_min: float, ascent_m: float,
                               rider_weight_kg: float, **kwargs) -> float:
    """Mean power in W/kg of rider weight, the unit of the model's mean_power_per_kg."""
    return estimate_mean_power(distance_km, duration_min, ascent_m, rider_weight_kg, **kwargs) / rider_weight_kg

if __name__ == "__main__":
    # 40 km in 80 min (30 km/h) with 300 m of climbing, 75 kg rider
    watts = estimate_mean_power(40, 80, 300, 75)
    print(f"flat-ish ride:  {watts:.0f} W, {watts / 75:.2f} W/kg")
    # climb test: 5 km at 7 % (350 m) in 20 min, 75 kg rider
    watts = estimate_mean_power(5, 20, 350, 75)
    print(f"climb test:     {watts:.0f} W, {watts / 75:.2f} W/kg")
