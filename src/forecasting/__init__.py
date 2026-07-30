"""
Forecasting package — solar/wind power prediction.

Production backend uses Random Forest (solar) and XGBoost (wind).
LSTM artifacts remain available offline but are not loaded on Railway.
"""

from src.forecasting.data_preprocessing import load_solar_features, prepare_forecast_frame
from src.forecasting.evaluator import evaluate_regression, metrics_dict

__all__ = [
    "load_solar_features",
    "prepare_forecast_frame",
    "evaluate_regression",
    "metrics_dict",
]
