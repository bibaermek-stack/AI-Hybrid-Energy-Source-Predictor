import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/processed")
df = pd.read_csv(DATA_PATH /"solar_cleaned.csv")

df["DATE_TIME"] = pd.to_datetime(df["DATE_TIME"])
#time based features
df["hour"] = df["DATE_TIME"].dt.hour
df["day"] = df["DATE_TIME"].dt.day
df["month"] = df["DATE_TIME"].dt.month

#daytime flag (solar works mostly 6AM-6PM)

df["is_daytime"] = df["hour"].apply(lambda x: 1 if 6 <= x <= 18 else 0)

print(df.head())
print(df.shape)

#save new dataset

df.to_csv("data/processed/build_features.csv", index=False)
print(" Feature dataset saved")