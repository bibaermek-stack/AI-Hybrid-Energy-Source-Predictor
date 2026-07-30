import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from models.solar_model import get_solar_model
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


DATA_PATH = Path("data/processed")
ARTIFACT_PATH = Path("artifacts")
ARTIFACT_PATH.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH / "build_features.csv")

x = df[[
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "hour",
    "day",
    "month"
]]

y = df["AC_POWER"]

x_train, x_test, y_train, y_test = train_test_split(
    x,y, test_size=0.2, random_state=42
)

model = get_solar_model()

model.fit(x_train,y_train)
preds = model.predict(x_test)
mae = mean_absolute_error(y_test, preds)
print("MAE:", mae)



joblib.dump(model, ARTIFACT_PATH / "solar_model.pkl")
print("Model saved successfully")

print(df["AC_POWER"].min(), df["AC_POWER"].max())