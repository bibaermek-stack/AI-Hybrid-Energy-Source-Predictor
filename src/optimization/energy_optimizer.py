import joblib
import pandas as pd
from pathlib import Path

ARTIFACT_PATH = Path("artifacts")

solar_model = joblib.load(ARTIFACT_PATH / "solar_model.pkl")
wind_model = joblib.load(ARTIFACT_PATH / "wind_model.pkl")


def predict_energy(solar_features, wind_features):

    solar_pred = solar_model.predict([solar_features])[0]
    wind_pred = wind_model.predict([wind_features])[0]

    if solar_pred > wind_pred:
        source = "Solar"
    else:
        source = "Wind"

    return {
        "solar_power": solar_pred,
        "wind_power": wind_pred,
        "best_source": source
    }


if __name__ == "__main__":

    solar_input = [800, 32, 40, 12, 15, 6]
    wind_input = [6.5, 260, 700]

    result = predict_energy(solar_input, wind_input)

    print(result)