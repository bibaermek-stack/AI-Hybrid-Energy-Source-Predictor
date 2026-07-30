import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.wind_model import get_wind_model
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


DATA_PATH = Path("data/raw")
ARTIFACT_PATH = Path("artifacts")
ARTIFACT_PATH.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH / "wind.csv", sep=",")
print(df.columns)
x = df[[
    "Wind Speed (m/s)",
    "Wind Direction (°)",
    "Theoretical_Power_Curve (KWh)"
]]
print(df.columns)
y = df["LV ActivePower (kW)"]

x_train, x_test, y_train, y_test = train_test_split(
    x,y, test_size=0.2, random_state=42
)

model = get_wind_model()

model.fit(x_train,y_train)
preds = model.predict(x_test)
mae = mean_absolute_error(y_test, preds)
print("Wind MAE:", mae)

joblib.dump(model, ARTIFACT_PATH / "wind_model.pkl")
print("Model saved successfully")

