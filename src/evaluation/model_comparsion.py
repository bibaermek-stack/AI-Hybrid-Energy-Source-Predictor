import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor

from xgboost import XGBRegressor


DATA_PATH = Path("data/processed")

df = pd.read_csv(DATA_PATH / "build_features.csv")

# FEATURES
X = df[[
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "hour",
    "day",
    "month"
]]

# TARGET
y = df["AC_POWER"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

models = {
    "Linear Regression": LinearRegression(),

    "Decision Tree": DecisionTreeRegressor(
        max_depth=10
    ),

    "Random Forest": RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    ),

    "XGBoost": XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6
    )
}

results = {}

for name, model in models.items():

    print(f"\nTraining {name}...")

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)

    results[name] = mae

    print(f"{name} MAE: {mae}")


print("\n==============================")
print("MODEL COMPARISON")
print("==============================")

for model, score in results.items():
    print(f"{model}: {score}")


best_model = min(results, key=results.get)

print("\nBest Model:", best_model)

import joblib
if best_model == "Random Forest":
    joblib.dump(models["Random Forest"], "artifacts/solar_rf_model.pkl")