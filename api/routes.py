from fastapi import APIRouter, HTTPException, Depends
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import os
import sys
from dotenv import load_dotenv
from src.optimization.hybrid_optimizer import optimize_energy
from api.schemas import (
    PredictionRequest, PredictionResponse, ExplanationRequest, ExplanationResponse,
    ForecastRequest, ForecastResponse, ChatRequest, ChatResponse, ForecastBatchRequest, ForecastBatchResponse,
    SolarmanProcessRequest, SolarmanProcessResponse, SolarmanRoiRequest, SolarmanRoiResponse,
    SolarmanAlertRequest, SolarmanAlertResponse
)
from api.security import require_api_key
from src.monitoring.model_monitor import PredictionLogger
from src.llm_agent.energy_advisor import explain_energy, chat_advisor
from src.utils.solarman_processor import SolarmanProcessor
from src.utils.solarman_client import (
    SolarmanClient,
    SolarmanAPIError,
    get_live_dashboard,
    demo_history_series,
    set_runtime_credentials,
    credentials_status,
)
from pydantic import BaseModel, Field

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

ARTIFACT_PATH = Path(os.getenv("MODEL_PATH", "artifacts")).resolve()

predictor_logger = PredictionLogger()

solar_model = None
wind_model = None

try:
    solar_model = joblib.load(ARTIFACT_PATH / "solar_model.pkl")
    logger.info("Solar model loaded successfully")
except FileNotFoundError as e:
    logger.error(f"Solar model not found at {ARTIFACT_PATH / 'solar_model.pkl'}: {e}")
except Exception as e:
    logger.error(f"Error loading solar model: {e}")

try:
    wind_model = joblib.load(ARTIFACT_PATH / "wind_model.pkl")
    logger.info("Wind model loaded successfully")
except FileNotFoundError as e:
    logger.error(f"Wind model not found at {ARTIFACT_PATH / 'wind_model.pkl'}: {e}")
except Exception as e:
    logger.error(f"Error loading wind model: {e}")


@router.get("/health")
def health_check():
    """Model health for the dashboard (RF solar + XGB wind). No TensorFlow/LSTM."""
    return {
        "status": "healthy" if solar_model and wind_model else "degraded",
        # Marks a backend that actually mounts the feature routes; clients use
        # this to avoid locking onto a stub that only answers /health.
        "api": "full",
        "models_loaded": {
            "solar": solar_model is not None,
            "wind": wind_model is not None,
            # Kept for older UI keys: forecast available iff solar RF is loaded
            "forecast": solar_model is not None,
            "lstm": solar_model is not None,
        },
        "forecast_backend": "random_forest",
        "python": sys.version.split()[0],
    }


def _rf_forecast_from_sequences(seqs: np.ndarray) -> list[float]:
    """
    Each sequence is (24, 6) features; use last timestep for solar_model.pkl.
    Columns: IRRADIATION, AMBIENT_TEMPERATURE, MODULE_TEMPERATURE, hour, day, month.
    """
    if solar_model is None:
        raise RuntimeError("solar_model not loaded")
    if len(seqs.shape) != 3 or seqs.shape[2] != 6:
        raise ValueError(f"Expected (B, T, 6), got {seqs.shape}")
    last = seqs[:, -1, :]
    try:
        X = pd.DataFrame(
            last,
            columns=[
                "IRRADIATION",
                "AMBIENT_TEMPERATURE",
                "MODULE_TEMPERATURE",
                "hour",
                "day",
                "month",
            ],
        )
        raw = solar_model.predict(X)
    except Exception:
        raw = solar_model.predict(last)
    return [max(0.0, float(p)) for p in raw]


@router.post("/forecast", response_model=ForecastResponse)
async def forecast_solar(request: ForecastRequest):
    """Forecast solar power for one 24×6 sequence via RandomForest solar_model."""
    try:
        seq = np.array(request.sequence, dtype=float)
        if seq.shape != (24, 6):
            raise HTTPException(
                status_code=400,
                detail=f"Sequence shape must be (24, 6), got {seq.shape}",
            )
        if solar_model is None:
            raise HTTPException(status_code=503, detail="solar_model.pkl not loaded")
        preds = _rf_forecast_from_sequences(np.expand_dims(seq, axis=0))
        return ForecastResponse(predicted_solar_power=preds[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Forecasting failed due to an internal error: {str(e)}",
        )


@router.post("/forecast-batch", response_model=ForecastBatchResponse)
async def forecast_solar_batch(request: ForecastBatchRequest):
    """Batch forecast (B, 24, 6) using RandomForest solar_model.pkl."""
    try:
        seqs = np.array(request.sequences, dtype=float)
        if len(seqs.shape) != 3 or seqs.shape[1] != 24 or seqs.shape[2] != 6:
            raise HTTPException(
                status_code=400,
                detail=f"Sequences shape must be (B, 24, 6), got {seqs.shape}",
            )
        if solar_model is None:
            raise HTTPException(
                status_code=503,
                detail="solar_model.pkl not loaded — forecast unavailable.",
            )
        predictions = _rf_forecast_from_sequences(seqs)
        return ForecastBatchResponse(predictions=predictions, model="random_forest")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch forecasting failed due to an internal error: {str(e)}",
        )



@router.post("/predict", response_model=PredictionResponse)
def predict_energy(request: PredictionRequest):
    """
    Predict energy output from solar and wind sources.
    
    Pydantic automatically validates all input ranges.
    """
    
    
    if solar_model is None or wind_model is None:
        logger.error("Models not loaded")
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. API is unavailable."
        )
    
    try:

        solar_features = pd.DataFrame([[
        request.irradiation,
        request.temperature,
        request.module,
        request.hour,
        request.day,
        request.month
        ]], columns=[
            "IRRADIATION",
            "AMBIENT_TEMPERATURE",
            "MODULE_TEMPERATURE",
            "hour",
            "day",
            "month"
        ])
        
        wind_features = pd.DataFrame([[
            request.wind_speed,
            request.direction,
            request.theoretical
        ]], columns=[
            "Wind Speed (m/s)",
            "Wind Direction (°)",
            "Theoretical_Power_Curve (KWh)"
        ])
        print("solar_input:" ,solar_features)
        print("wind_input:" ,wind_features)

       
        solar = max(0.0, float(solar_model.predict(solar_features)[0]))
        wind = max(0.0, float(wind_model.predict(wind_features)[0]))

        if np.isnan(solar) or np.isnan(wind):
            logger.error(f"Model returned NaN: solar={solar}, wind={wind}")
            raise HTTPException(
                status_code=500,
                detail="Model returned invalid prediction (NaN)"
            )
        
        if np.isinf(solar) or np.isinf(wind):
            logger.error(f"Model returned Inf: solar={solar}, wind={wind}")
            raise HTTPException(
                status_code=500,
                detail="Model returned invalid prediction (Inf)"
            )

        
        result = optimize_energy(
            solar,
            wind,
            load_kw=request.load_kw,
            battery_kw=request.battery_kw,
            solar_cost_per_kwh=request.solar_cost_per_kwh,
            wind_cost_per_kwh=request.wind_cost_per_kwh,
            strategy=request.strategy,
        )
        
        predictor_logger.log_prediction(
            inputs={
                "irradiation": request.irradiation,
                "temperature": request.temperature,
                "module": request.module,
                "hour": request.hour,
                "day": request.day,
                "month": request.month,
                "wind_speed": request.wind_speed,
                "direction": request.direction,
                "theoretical": request.theoretical,
                "load_kw": request.load_kw,
                "battery_kw": request.battery_kw,
                "strategy": request.strategy,
            },
            solar=solar,
            wind=wind,
            recommendation=result["recommended_source"]
        )
        
        logger.info(
            f"Prediction: solar={solar:.2f}, wind={wind:.2f}, "
            f"recommendation={result['recommended_source']}, "
            f"reliability={result.get('reliability_index')}"
        )
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Prediction failed due to an internal error"
        )


@router.post("/explain", response_model=ExplanationResponse)
def explain_recommendation(request: ExplanationRequest):
    """
    Provide an explanation for the recommended energy source.
    """
    try:
        explanation = explain_energy(request.source, lang=request.lang)
        return ExplanationResponse(explanation=explanation)
    except Exception as e:
        logger.error(f"Error in explanation route: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Explanation generation failed"
        )


@router.post("/chat", response_model=ChatResponse)
def chat_with_advisor(request: ChatRequest):
    """
    Chat with the RAG energy advisor.
    """
    try:
        response = chat_advisor(request.query, lang=request.lang)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error in chat route: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Chatbot communication failed"
        )


@router.post("/solarman/process", response_model=SolarmanProcessResponse)
def process_solarman_data(request: SolarmanProcessRequest):
    """
    Parse Solarman payload and calculate Performance Ratio metrics.
    """
    try:
        processor = SolarmanProcessor(dc_capacity_kwp=request.dc_capacity_kwp)
        parsed = processor.parse_current_data(request.payload)
        pr_metrics = processor.calculate_performance_ratio(
            parsed, request.irradiance_w_m2, request.ambient_temp_c
        )
        return {
            "parsed_data": parsed,
            **pr_metrics
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing Solarman data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while processing Solarman data")


@router.post("/solarman/roi", response_model=SolarmanRoiResponse)
def calculate_solarman_roi(request: SolarmanRoiRequest):
    """
    Calculate financial metrics including Dynamic Payback and ROI.
    """
    try:
        processor = SolarmanProcessor(dc_capacity_kwp=1.0)
        roi_metrics = processor.calculate_roi_metrics(
            total_generation_kwh=request.total_generation_kwh,
            initial_investment_kzt=request.initial_investment_kzt,
            tariff_kzt_per_kwh=request.tariff_kzt_per_kwh,
            opex_annual_kzt=request.opex_annual_kzt,
            annual_degradation=request.annual_degradation,
            inflation_rate=request.inflation_rate,
            lifetime_years=request.lifetime_years
        )
        return roi_metrics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating ROI metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while calculating ROI metrics")


@router.get("/solarman/weather")
def get_turkistan_weather_forecast():
    """
    Retrieve Turkistan weather metadata.
    """
    try:
        processor = SolarmanProcessor(dc_capacity_kwp=1.0)
        return processor.fetch_turkistan_weather()
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching weather data")


@router.post("/solarman/alert", response_model=SolarmanAlertResponse)
def check_and_alert_solarman(request: SolarmanAlertRequest):
    """
    Check system status and trigger Telegram bot alerts if offline or faulty.
    """
    try:
        processor = SolarmanProcessor(dc_capacity_kwp=1.0)
        alert_info = processor.check_status_and_alert(
            parsed_data=request.parsed_data,
            telegram_token=request.telegram_token,
            chat_id=request.chat_id
        )
        return alert_info
    except Exception as e:
        logger.error(f"Error executing status check and alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while executing status check and alert")


class SolarmanCredsRequest(BaseModel):
    app_id: str = Field(..., min_length=1)
    app_secret: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1, description="Plain password or SHA256 hex")
    device_sn: str = Field("2501221272")
    device_id: str | None = Field(None)
    base_url: str = Field("https://globalapi.solarmanpv.com")
    password_is_sha256: bool = Field(False)
    test_auth: bool = Field(True, description="Try token request after saving")


@router.post("/solarman/configure", dependencies=[Depends(require_api_key)])
def solarman_configure(req: SolarmanCredsRequest):
    """
    Register Solarman OpenAPI credentials for this API process, then optionally
    validate with a real token request.

    Requires the `X-API-Key` header (see ECOPREDICT_API_KEY) — this route rewrites
    the credentials every other Solarman endpoint authenticates with.
    """
    status = set_runtime_credentials(
        app_id=req.app_id,
        app_secret=req.app_secret,
        email=req.email,
        password=req.password,
        device_sn=req.device_sn,
        device_id=req.device_id or "",
        base_url=req.base_url,
        password_is_sha256=req.password_is_sha256,
    )
    auth_ok = False
    auth_error = None
    if req.test_auth:
        try:
            client = SolarmanClient()
            client.authenticate(force=True)
            auth_ok = True
            # try resolve device
            try:
                did, sn = client.resolve_device()
                status["device_id"] = did
                status["device_sn"] = sn
            except Exception as re:
                status["device_resolve_warning"] = str(re)
        except Exception as e:
            auth_error = str(e)
    return {
        **status,
        "auth_ok": auth_ok,
        "auth_error": auth_error,
        "message": "Credentials stored. Call GET /solarman/live?demo=false for real data."
        if auth_ok
        else "Credentials stored but auth failed — check APP ID/secret/email/password.",
    }


@router.get("/solarman/live")
def solarman_live_device(
    demo: bool = False,
    force_demo: bool = False,
    device_sn: str | None = None,
):
    """
    Full live dashboard for a Solarman inverter.

    Default SN 2501221272; pass ``device_sn=2411046235`` for the second unit.
    **Real API by default** when credentials are configured (POST /solarman/configure
    or .env). Use force_demo=true only for offline screenshot sample.
    demo=true allows silent fallback to sample data if API fails.
    """
    try:
        # Prefer real API; only fall back if demo=true
        return get_live_dashboard(
            use_demo_if_no_creds=demo or force_demo,
            force_demo=force_demo,
            device_sn=device_sn,
        )
    except SolarmanAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error("solarman live failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solarman/history")
def solarman_history(days: int = 1, demo: bool = False):
    """
    Historical series for charts from Solarman OpenAPI.
    """
    from datetime import datetime, timedelta

    client = SolarmanClient()
    if not client.credentials_configured:
        if not demo:
            raise HTTPException(
                status_code=400,
                detail="No Solarman credentials. POST /solarman/configure first.",
            )
        return {
            "source": "demo",
            "series": demo_history_series(24 * max(1, min(days, 7))),
        }

    try:
        end = datetime.now()
        start = end - timedelta(days=max(1, min(days, 31)))
        hist = client.get_historical(
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d"),
            time_type=1 if days <= 1 else 2,
        )
        from src.utils.solarman_client import parse_historical_for_charts

        series = parse_historical_for_charts(hist)
        if not series and demo:
            series = demo_history_series(24)
        return {"source": "api", "series": series, "raw": hist}
    except Exception as e:
        if demo:
            return {
                "source": "demo_fallback",
                "series": demo_history_series(24),
                "error": str(e),
            }
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/solarman/status", dependencies=[Depends(require_api_key)])
def solarman_credentials_status():
    """
    Whether Solarman OpenAPI credentials are present.

    Guarded: the response discloses the configured device SN / ID and which
    credential fields are set.
    """
    return credentials_status()


@router.get("/solarman/forecast")
def get_solarman_generation_forecast(dc_capacity_kwp: float = 50.0):
    """
    Fetch 24-hour weather forecast for Turkistan and predict hourly solar generation.
    Uses the new solar_forecast_rf.pkl (22 features) with iterative lag computation.
    Falls back to old solar_model.pkl if new model not found.
    """
    try:
        from datetime import datetime
        import pickle as pkl
        import numpy as np
        import pandas as pd

        processor = SolarmanProcessor(dc_capacity_kwp=dc_capacity_kwp)
        weather_data = processor.fetch_turkistan_hourly_forecast()

        if "error" in weather_data:
            raise HTTPException(status_code=500, detail=f"Failed to fetch forecast: {weather_data['error']}")

        forecast_list = weather_data["forecast"]

        # ── Try to load new solar_forecast_rf + scaler ──────────────────────
        new_rf_path     = ARTIFACT_PATH / "solar_forecast_rf.pkl"
        new_xgb_path    = ARTIFACT_PATH / "solar_forecast_xgb.pkl"
        new_scaler_path = ARTIFACT_PATH / "solar_forecast_scaler.pkl"

        use_new_model = (
            new_rf_path.exists() and
            new_scaler_path.exists()
        )

        if use_new_model:
            logger.info("Using solar_forecast_rf.pkl (22-feature model) for forecast")
            with open(new_rf_path, "rb") as f:
                new_rf = pkl.load(f)
            with open(new_scaler_path, "rb") as f:
                scaler_data = pkl.load(f)
            feat_scaler  = scaler_data["scaler"]
            feat_names   = scaler_data["features"]

            # Load XGBoost for ensemble (optional)
            new_xgb = None
            if new_xgb_path.exists():
                try:
                    with open(new_xgb_path, "rb") as f:
                        new_xgb = pkl.load(f)
                except Exception:
                    pass

            # Reference plant capacity used during training (Plant 1 aggregated)
            TRAIN_CAPACITY_KWP = 1250.0

            # ── Build iterative forecast with rolling lag ──────────────────
            # Seed lags with zeros (before sunrise, power=0)
            ac_history   = [0.0] * 4   # last 4 AC_POWER values for rolling
            irr_history  = [0.0] * 4   # last 4 IRRADIATION values

            irrad_max = 0.95   # normalisation constant (kW/m2) matching training

            predictions = []

            for hour_data in forecast_list:
                time_str = hour_data["time"]
                try:
                    dt = datetime.fromisoformat(time_str)
                except Exception:
                    dt = datetime.now()

                irrad_wm2 = float(hour_data.get("shortwave_radiation", 0.0))
                temp      = float(hour_data.get("temperature", 25.0))
                # Convert W/m2 → kW/m2 to match training data units
                irrad_kwm2 = irrad_wm2 / 1000.0

                module_temp = temp + irrad_kwm2 * ((processor.noct - 20.0) / 800.0)
                temp_delta  = module_temp - temp
                irrad_norm  = min(irrad_kwm2 / irrad_max, 1.0)

                hour      = dt.hour
                minute    = dt.minute
                month     = dt.month
                weekday   = dt.weekday()
                is_day    = 1 if 6 <= hour <= 19 else 0

                hour_sin  = np.sin(2 * np.pi * hour  / 24)
                hour_cos  = np.cos(2 * np.pi * hour  / 24)
                month_sin = np.sin(2 * np.pi * month / 12)
                month_cos = np.cos(2 * np.pi * month / 12)

                ac_lag1  = ac_history[-1]
                ac_lag3  = ac_history[-3] if len(ac_history) >= 3 else 0.0
                ac_roll4 = float(np.mean(ac_history[-4:]))
                ac_std4  = float(np.std(ac_history[-4:])) if len(ac_history) >= 2 else 0.0

                irr_lag1  = irr_history[-1]
                irr_lag3  = irr_history[-3] if len(irr_history) >= 3 else 0.0
                irr_roll4 = float(np.mean(irr_history[-4:]))
                irr_std4  = float(np.std(irr_history[-4:])) if len(irr_history) >= 2 else 0.0

                row = np.array([[
                    irrad_kwm2, temp, module_temp,
                    hour, minute, month, weekday,
                    hour_sin, hour_cos, month_sin, month_cos,
                    is_day, temp_delta, irrad_norm,
                    ac_lag1,  ac_lag3,  ac_roll4,  ac_std4,
                    irr_lag1, irr_lag3, irr_roll4, irr_std4
                ]])

                row_scaled = feat_scaler.transform(row)

                # ── Ensemble prediction ──────────────────────────────────
                pred_rf  = float(new_rf.predict(row_scaled)[0])
                if new_xgb is not None:
                    pred_xgb = float(new_xgb.predict(row_scaled)[0])
                    raw_pred = (pred_rf * 0.5 + pred_xgb * 0.5)
                else:
                    raw_pred = pred_rf

                raw_pred = max(0.0, raw_pred)

                # Scale from training plant capacity to user plant capacity
                pred_power = raw_pred * (dc_capacity_kwp / TRAIN_CAPACITY_KWP)

                # Hard clamp: if no sunlight, power must be zero
                # (lag features can carry phantom power into nighttime)
                if irrad_wm2 <= 0.0:
                    pred_power = 0.0
                else:
                    pred_power = max(0.0, pred_power)

                # Update rolling buffers for next timestep (autoregressive)
                ac_history.append(raw_pred)
                irr_history.append(irrad_kwm2)
                if len(ac_history) > 4:
                    ac_history.pop(0)
                if len(irr_history) > 4:
                    irr_history.pop(0)

                predictions.append({
                    "time": time_str,
                    "hour": hour,
                    "temperature": temp,
                    "cloud_cover": float(hour_data.get("cloud_cover", 0.0)),
                    "irradiance": irrad_wm2,
                    "uv_index": float(hour_data.get("uv_index", 0.0)),
                    "predicted_power_kw": round(pred_power, 3)
                })

        else:
            # ── Fallback: old solar_model.pkl (6 features) ────────────────
            logger.warning("solar_forecast_rf.pkl not found, falling back to solar_model.pkl")
            if solar_model is None:
                raise HTTPException(status_code=503, detail="No solar model loaded.")

            predictions = []
            for hour_data in forecast_list:
                time_str = hour_data["time"]
                try:
                    dt = datetime.fromisoformat(time_str)
                except Exception:
                    dt = datetime.now()

                irrad = float(hour_data.get("shortwave_radiation", 0.0))
                temp  = float(hour_data.get("temperature", 25.0))
                irrad_scaled = irrad / 1000.0
                module_temp  = temp + irrad_scaled * ((processor.noct - 20.0) / 800.0)

                features = pd.DataFrame([[
                    irrad_scaled, temp, module_temp,
                    dt.hour, dt.day, dt.month
                ]], columns=[
                    "IRRADIATION", "AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE",
                    "hour", "day", "month"
                ])
                raw_pred = float(solar_model.predict(features)[0])
                pred_power = max(0.0, raw_pred * (dc_capacity_kwp / 1250.0))

                predictions.append({
                    "time": time_str,
                    "hour": dt.hour,
                    "temperature": temp,
                    "cloud_cover": float(hour_data.get("cloud_cover", 0.0)),
                    "irradiance": irrad,
                    "uv_index": float(hour_data.get("uv_index", 0.0)),
                    "predicted_power_kw": round(pred_power, 3)
                })

        return {"forecasts": predictions}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in solarman forecast endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))