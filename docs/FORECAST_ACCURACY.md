# How accurate the solar forecast is

The Training screen shows the solar model's **R² = 0.997**, from
`artifacts/model_metrics.json`. That number is not the forecast's accuracy.

## What the 0.997 measures

`solar_model.pkl` is a RandomForest trained by `src/training/train_pipeline.py`
on Kaggle's Plant 1 data, `data/processed/build_features.csv` (34 days). Its
inputs include **the irradiance measured at the plant** at that moment.
Re-measured on the same data:

| Setup | Daytime R² | Daytime MAE |
|---|---|---|
| Random split of 15-minute rows (as trained) | 0.993 | 20 kW (1.5% of peak) |
| Time split: train on the first 27 days, test on the last 7 | 0.992 | 20 kW (1.5%) |
| Just `AC = k × IRRADIATION`, time split | 0.981 | 36 kW (2.7%) |

The split was not the problem: a time split gives the same number. The model
turns *measured* sunlight into power, and a straight line nearly does the
same. The number says nothing about forecasting the weather.

## What the forecast actually does

`GET /solarman/forecast`, used by the app's Forecast screen:

1. It takes WeatherAPI's hourly forecast for Turkistan.
2. WeatherAPI's sunlight field (`short_rad`) was never read, so the
   irradiance came from **cloud cover and a sine curve**:
   `950 × sin(π(h−6)/12) × (1 − 0.75 × cloud)`. That curve has fixed sunrise
   and sunset at 06:00 and 18:00 and ignores the season.
3. That value goes into the model above.
4. The result is scaled to **50 kWp**, which the phone always sent, whatever
   the station's size.

The same model on the same 7 test days, fed the sine formula:

| Input | Daytime R² | Daytime MAE |
|---|---|---|
| Measured irradiance | 0.992 | 1.5% of peak |
| Sine formula with the day's true total energy (an oracle; no forecast knows it) | 0.80 | 8.4% of peak |
| Sine formula, clear sky | 0.24 | 17.9% of peak |

A real cloud forecast adds its own error on top of these.

## Measuring it on the station: `GET /forecast/backtest?days=14`

`src/forecasting/backtest.py` runs on the server, where the Solarman
credentials are. It gathers, for each of the last 14 complete days:

- **Actual:** the station's hourly mean AC power, from Solarman's historical
  API (5-minute frames, station time UTC+5).
- **Weather as it was forecast:** Open-Meteo's historical forecast API, which
  keeps the archived model runs. It gives hourly GHI, temperature and cloud
  cover, and needs no key.

It scores these methods on the same sunlit hours of the later 7 days:

| Method | What it is |
|---|---|
| `app` | What the Forecast screen showed: sine formula → RandomForest, scaled to 50 kWp |
| `app_rated` | The same, scaled to the station's rated power (`SOLARMAN_RATED_KW`) |
| `rf_ghi` | RandomForest fed with the forecast GHI instead of the sine formula |
| `pv` | Physical model: rated kW × GHI/1000 × temperature loss × PR. The performance ratio PR is fitted on the first 7 days only. |
| `persistence` | Yesterday's actual at the same hour; a forecast should beat it |

Reported per method:
- MAE in kW and as % of rated power;
- bias;
- RMSE and R²;
- the error of each day's total energy.

The result is cached for 6 hours. Backend health requests it every 6 hours and
prints the table, so the numbers are visible in the workflow log.

Where the result shows up:
- The app's Forecast screen shows the measured error of the method it uses.
- The Training screen says the R² above is not that number.

## Changes that follow from this

- **Capacity:** `/solarman/forecast` now defaults to the station's rated power.
  The app no longer sends 50 kWp; older app versions still do, and still get
  what they ask for.
- **Sunlight source:** WeatherAPI's `short_rad` is used when the forecast has
  it. Each hour records whether its sunlight was forecast or estimated
  (`radiation_source`), and the response says which (`irradiance_source`).
- **Next step:** once the station numbers are in, switch the forecast to the
  method with the lowest measured error. Judging from Plant 1, that will
  probably be `pv` or `rf_ghi`.
