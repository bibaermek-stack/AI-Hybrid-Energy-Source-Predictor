import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import numpy as np
import joblib

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

from models.lstm_model import get_lstm_model


DATA_PATH = Path("data/processed")
ARTIFACT_PATH = Path("artifacts")

df = pd.read_csv(DATA_PATH / "build_features.csv")

features = [
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "hour",
    "day",
    "month"
]

target = "AC_POWER"

X = df[features].values
y = df[target].values

# Scale both inputs and targets separately
scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

X_scaled = scaler_X.fit_transform(X)
y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

def create_sequences(X, y, seq_len=24):
    X_seq = []
    y_seq = []
    for i in range(len(X) - seq_len):
        X_seq.append(X[i:i+seq_len])
        y_seq.append(y[i+seq_len])
    return np.array(X_seq), np.array(y_seq)

X_seq, y_seq = create_sequences(X_scaled, y_scaled)

split = int(len(X_seq) * 0.8)
X_train = X_seq[:split]
X_test = X_seq[split:]
y_train = y_seq[:split]
y_test = y_seq[split:]

model = get_lstm_model((X_train.shape[1], X_train.shape[2]))

model.fit(
    X_train,
    y_train,
    epochs=25,
    batch_size=32,
    validation_split=0.1
)

preds_scaled = model.predict(X_test)
# Inverse scale predictions and actual values to calculate actual MAE
preds = scaler_y.inverse_transform(preds_scaled).flatten()
y_test_original = scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()

mae = mean_absolute_error(y_test_original, preds)
print("LSTM MAE (original scale):", mae)

model.save(ARTIFACT_PATH / "solar_lstm_model.h5")
# Save both scalers in a dictionary
joblib.dump({"scaler_X": scaler_X, "scaler_y": scaler_y}, ARTIFACT_PATH / "lstm_scaler.pkl")
print("LSTM model saved")