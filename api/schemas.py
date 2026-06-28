from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    """Validated prediction request"""
    irradiation: float = Field(..., ge=0, le=1500, description="Solar irradiation in W/m²")
    temperature: float = Field(..., ge=-20, le=60, description="Ambient temperature in °C")
    module: float = Field(..., ge=-10, le=80, description="Module temperature in °C")
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day: int = Field(..., ge=1, le=31, description="Day of month (1-31)")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    wind_speed: float = Field(..., ge=0, le=30, description="Wind speed in m/s")
    direction: float = Field(..., ge=0, le=360, description="Wind direction in degrees")
    theoretical: float = Field(..., ge=0, le=5000, description="Theoretical power in kW")

class PredictionResponse(BaseModel):
    """Prediction response"""
    solar_power: float = Field(..., description="Solar power output in kW")
    wind_power: float = Field(..., description="Wind power output in kW")
    total_energy: float = Field(..., description="Total energy output in kW")
    recommended_source: str = Field(..., description="Recommended energy source")

class ExplanationRequest(BaseModel):
    """Explanation request schema"""
    source: str = Field(..., description="Recommended energy source ('Solar' or 'Wind')")
    lang: str = Field("en", description="Language of explanation ('en' or 'kk')")

class ExplanationResponse(BaseModel):
    """Explanation response schema"""
    explanation: str = Field(..., description="Explanation of the recommendation")

class ForecastRequest(BaseModel):
    """Sequence of 24 hourly weather features"""
    sequence: list[list[float]] = Field(..., description="24x6 list representing the sequence of weather features")

class ForecastResponse(BaseModel):
    """Forecast response"""
    predicted_solar_power: float = Field(..., description="Predicted solar power output in kW")

class ChatRequest(BaseModel):
    """Chat request schema"""
    query: str = Field(..., description="User question about hybrid energy")
    lang: str = Field("en", description="Language of request ('en' or 'kk')")

class ChatResponse(BaseModel):
    """Chat response schema"""
    response: str = Field(..., description="Chatbot answer")

class ForecastBatchRequest(BaseModel):
    """List of 24x6 sequences of features for batch forecasting"""
    sequences: list[list[list[float]]] = Field(..., description="List of 24x6 sequences")

class ForecastBatchResponse(BaseModel):
    """Batch forecast response"""
    predictions: list[float] = Field(..., description="List of predicted solar power outputs in kW")




