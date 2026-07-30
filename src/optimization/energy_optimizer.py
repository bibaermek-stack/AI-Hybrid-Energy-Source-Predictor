"""
Convenience wrapper: load models and run hybrid dispatch.

Prefer using the FastAPI `/predict` route in production so models are loaded once.
"""

from pathlib import Path

import joblib

from src.optimization.hybrid_optimizer import optimize_energy

ARTIFACT_PATH = Path("artifacts")

solar_model = joblib.load(ARTIFACT_PATH / "solar_model.pkl")
wind_model = joblib.load(ARTIFACT_PATH / "wind_model.pkl")


def predict_energy(solar_features, wind_features, **dispatch_kwargs):
    solar_pred = float(solar_model.predict([solar_features])[0])
    wind_pred = float(wind_model.predict([wind_features])[0])
    result = optimize_energy(max(0.0, solar_pred), max(0.0, wind_pred), **dispatch_kwargs)
    # Alias for older callers
    result["best_source"] = result["recommended_source"]
    return result


if __name__ == "__main__":
    solar_input = [800, 32, 40, 12, 15, 6]
    wind_input = [6.5, 260, 700]
    print(predict_energy(solar_input, wind_input))
    print(predict_energy(solar_input, wind_input, load_kw=900, battery_kw=50))
