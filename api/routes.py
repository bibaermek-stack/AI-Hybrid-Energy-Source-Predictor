from fastapi import APIRouter, HTTPException, Depends
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import os
from dotenv import load_dotenv
from src.optimization.hybrid_optimizer import optimize_energy
from api.schemas import PredictionRequest, PredictionResponse, ExplanationRequest, ExplanationResponse, ForecastRequest, ForecastResponse, ChatRequest, ChatResponse, ForecastBatchRequest, ForecastBatchResponse
from src.monitoring.model_monitor import PredictionLogger
from src.llm_agent.energy_advisor import explain_energy, chat_advisor

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

ARTIFACT_PATH = Path(os.getenv("MODEL_PATH", "artifacts")).resolve()

predictor_logger = PredictionLogger()

solar_model = None
wind_model = None
lstm_model = None
lstm_scaler = None

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

try:
    import tensorflow as tf
    try:
        # Load keras model (solar_lstm_model.h5)
        lstm_model = tf.keras.models.load_model(ARTIFACT_PATH / "solar_lstm_model.h5", compile=False)
        lstm_scaler_data = joblib.load(ARTIFACT_PATH / "lstm_scaler.pkl")
        if isinstance(lstm_scaler_data, dict):
            lstm_scaler = lstm_scaler_data["scaler_X"]
            lstm_y_scaler = lstm_scaler_data["scaler_y"]
        else:
            lstm_scaler = lstm_scaler_data
            lstm_y_scaler = None
        logger.info("LSTM model and scaler loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"LSTM model or scaler not found: {e}")
    except Exception as e:
        logger.error(f"Error loading LSTM model: {e}")
except ImportError:
    logger.warning("Tensorflow is not installed. LSTM forecasting will be disabled.")



@router.get("/health")
def health_check():
    """Check if models are loaded and API is healthy"""
    return {
        "status": "healthy" if solar_model and wind_model else "unhealthy",
        "models_loaded": {
            "solar": solar_model is not None,
            "wind": wind_model is not None,
            "lstm": lstm_model is not None
        }
    }


@router.post("/forecast", response_model=ForecastResponse)
async def forecast_solar(request: ForecastRequest):
    """
    Forecast solar energy output using the LSTM model.
    """
    if lstm_model is None or lstm_scaler is None:
        logger.error("LSTM model not loaded")
        raise HTTPException(
            status_code=503,
            detail="LSTM model not loaded. Forecasting is unavailable."
        )
    
    try:
        seq = np.array(request.sequence)
        if seq.shape != (24, 6):
            raise HTTPException(
                status_code=400,
                detail=f"Sequence shape must be (24, 6), got {seq.shape}"
            )
        
        # Scale the sequence
        scaled_seq = lstm_scaler.transform(seq)
        
        # Reshape to (1, 24, 6) for model input
        input_data = np.expand_dims(scaled_seq, axis=0)
        
        # Predict
        pred = lstm_model(input_data, training=False).numpy()
        if lstm_y_scaler is not None:
            val = float(lstm_y_scaler.inverse_transform(pred)[0][0])
        else:
            val = float(pred[0][0])
        
        # Handle invalid predictions
        if np.isnan(val) or np.isinf(val):
            logger.error(f"LSTM returned invalid prediction: {val}")
            raise HTTPException(
                status_code=500,
                detail="LSTM model returned invalid prediction (NaN/Inf)"
            )
            
        return ForecastResponse(predicted_solar_power=max(0.0, val))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Forecasting failed due to an internal error: {str(e)}"
        )


@router.post("/forecast-batch", response_model=ForecastBatchResponse)
async def forecast_solar_batch(request: ForecastBatchRequest):
    """
    Forecast solar energy output for a batch of sequences using the LSTM model.
    """
    if lstm_model is None or lstm_scaler is None:
        logger.error("LSTM model not loaded")
        raise HTTPException(
            status_code=503,
            detail="LSTM model not loaded. Forecasting is unavailable."
        )
    
    try:
        seqs = np.array(request.sequences)
        # Expecting shape (B, 24, 6)
        if len(seqs.shape) != 3 or seqs.shape[1] != 24 or seqs.shape[2] != 6:
            raise HTTPException(
                status_code=400,
                detail=f"Sequences shape must be (B, 24, 6), got {seqs.shape}"
            )
        
        # We need to scale each sequence. Since the scaler scales 2D arrays, 
        # we can reshape to (B*24, 6), scale, and reshape back to (B, 24, 6).
        B = seqs.shape[0]
        flat_seqs = seqs.reshape(B * 24, 6)
        scaled_flat = lstm_scaler.transform(flat_seqs)
        scaled_seqs = scaled_flat.reshape(B, 24, 6)
        
        # Predict
        preds = lstm_model(scaled_seqs, training=False).numpy()
        if lstm_y_scaler is not None:
            preds_orig = lstm_y_scaler.inverse_transform(preds).flatten().tolist()
            predictions = [max(0.0, float(p)) for p in preds_orig]
        else:
            predictions = [max(0.0, float(p[0])) for p in preds]
        
        return ForecastBatchResponse(predictions=predictions)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch forecasting: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch forecasting failed due to an internal error: {str(e)}"
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

       
        solar = float(solar_model.predict(solar_features)[0])
        wind = float(wind_model.predict(wind_features)[0])

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

        
        result = optimize_energy(solar, wind)
        
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
                "theoretical": request.theoretical
            },
            solar=solar,
            wind=wind,
            recommendation=result["recommended_source"]
        )
        
        logger.info(f"Prediction: solar={solar:.2f}, wind={wind:.2f}, recommendation={result['recommended_source']}")
        
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