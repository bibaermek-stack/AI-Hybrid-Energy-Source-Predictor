import pandas as pd 
from pathlib import Path

RAW_DATA_PATH = Path("data/raw")
GEN_FILE = RAW_DATA_PATH / "Plant_1_Generation_Data.csv"
WEATHER_FILE =RAW_DATA_PATH / "Plant_1_Weather_Sensor_Data.csv"

def load_generation_data():
    generation_df = pd.read_csv(GEN_FILE)
    return generation_df
def load_weather_data():
    weather_df = pd.read_csv(WEATHER_FILE)
    return weather_df

if __name__ == "__main__":

    gen = load_generation_data()
    weather = load_weather_data()

    print("Generation Data Shape:", gen.shape)
    print("Weather Data Shape:", weather.shape)

    print("\nGeneration Sample")
    print(gen.head())

    print("\nWeather Sample")
    print(weather.head())