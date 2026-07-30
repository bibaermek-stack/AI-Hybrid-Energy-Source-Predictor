"""Forecast model factories (RF / XGB / optional LSTM)."""

from src.forecasting.models.rf_model import get_solar_rf_model, load_solar_rf
from src.forecasting.models.xgb_model import get_wind_model, load_wind_model

__all__ = [
    "get_solar_rf_model",
    "load_solar_rf",
    "get_wind_model",
    "load_wind_model",
]
