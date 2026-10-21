"""Deterministic educational gearing model. Not validated for real vehicle setup decisions."""
from __future__ import annotations

MODEL_VERSION = "gearing-tradeoff-0.1.0"
ASSUMPTIONS = [
    "Constant engine torque of 300 N·m at the selected engine speed.",
    "Selected gear ratio is fixed at 2.00:1.",
    "Drivetrain efficiency is fixed at 0.90.",
    "Effective wheel radius is fixed at 0.330 m.",
    "No aerodynamic drag, tyre slip, torque curve, shift time, gradient or limiter behaviour is modelled.",
    "Outputs are illustrative model estimates, not measured vehicle performance or lap-time predictions.",
]
PARAMETER = {
    "name": "Final drive ratio",
    "key": "final_drive_ratio",
    "unit": "ratio (dimensionless)",
    "minimum": 2.5,
    "maximum": 5.0,
    "baseline": 3.5,
    "step": 0.1,
    "definition": "Final-drive reduction between gearbox output and driven wheels.",
}
FIXED = {"engine_torque_nm": 300.0, "gear_ratio": 2.0, "drivetrain_efficiency": 0.90, "wheel_radius_m": 0.330, "engine_rpm": 8000.0}


def _calculate(final_drive_ratio: float) -> dict:
    wheel_torque_nm = FIXED["engine_torque_nm"] * FIXED["gear_ratio"] * final_drive_ratio * FIXED["drivetrain_efficiency"]
    tractive_force_n = wheel_torque_nm / FIXED["wheel_radius_m"]
    wheel_rpm = FIXED["engine_rpm"] / (FIXED["gear_ratio"] * final_drive_ratio)
    theoretical_speed_kmh = wheel_rpm * (2 * 3.141592653589793 * FIXED["wheel_radius_m"]) * 60 / 1000
    return {
        "wheel_torque_nm": round(wheel_torque_nm, 1),
        "tractive_force_n": round(tractive_force_n, 1),
        "theoretical_speed_kmh": round(theoretical_speed_kmh, 1),
    }


def run_experiment(final_drive_ratio: float, prediction: str, hypothesis: str) -> dict:
    if not 2.5 <= final_drive_ratio <= 5.0:
        raise ValueError("Final drive ratio must be between 2.5 and 5.0 (dimensionless).")
    if not hypothesis.strip():
        raise ValueError("Enter a hypothesis before running the experiment.")
    if not prediction.strip():
        raise ValueError("Record your prediction before running the experiment.")
    baseline = _calculate(PARAMETER["baseline"])
    changed = _calculate(float(final_drive_ratio))
    deltas = {key: round(changed[key] - baseline[key], 1) for key in changed}
    return {
        "model_version": MODEL_VERSION,
        "evidence_label": "SIMULATED",
        "parameter": {**PARAMETER, "value": float(final_drive_ratio)},
        "prediction": prediction.strip(),
        "hypothesis": hypothesis.strip(),
        "fixed_inputs": FIXED,
        "baseline": baseline,
        "result": changed,
        "delta_vs_baseline": deltas,
        "assumptions": ASSUMPTIONS,
        "limitations": "Educational gearing calculation only. Not validated against a real vehicle. Do not use for safety, setup, reliability, grip or lap-time decisions.",
        "uncertainty": "Not quantified. No confidence percentage is available.",
    }
