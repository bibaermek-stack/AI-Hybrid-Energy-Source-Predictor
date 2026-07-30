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
    # Optional hybrid dispatch controls (defaults preserve legacy behaviour)
    load_kw: float | None = Field(None, ge=0, description="Optional demand to serve (kW). None = full offtake")
    battery_kw: float = Field(0.0, ge=0, description="Optional battery discharge capacity (kW)")
    solar_cost_per_kwh: float = Field(1.0, ge=0, description="Relative solar LCOE for merit-order dispatch")
    wind_cost_per_kwh: float = Field(1.0, ge=0, description="Relative wind LCOE for merit-order dispatch")
    strategy: str = Field(
        "hybrid",
        description="Dispatch strategy: hybrid | min_cost | max_power | balanced",
    )

class PredictionResponse(BaseModel):
    """Prediction response"""
    solar_power: float = Field(..., description="Solar power available in kW")
    wind_power: float = Field(..., description="Wind power available in kW")
    total_energy: float = Field(..., description="Total renewable available in kW")
    recommended_source: str = Field(..., description="Recommended energy source (Solar | Wind | Hybrid)")
    solar_used: float | None = Field(None, description="Solar power dispatched to load (kW)")
    wind_used: float | None = Field(None, description="Wind power dispatched to load (kW)")
    battery_used: float | None = Field(None, description="Battery discharge used (kW)")
    load_kw: float | None = Field(None, description="Demand served against (kW)")
    shortfall_kw: float | None = Field(None, description="Unserved load after renewables+battery (kW)")
    curtailment_kw: float | None = Field(None, description="Curtailed renewable power (kW)")
    solar_share: float | None = Field(None, description="Share of renewable dispatch from solar [0-1]")
    wind_share: float | None = Field(None, description="Share of renewable dispatch from wind [0-1]")
    hybrid_share: float | None = Field(None, description="Mix index: 1=50/50, 0=single source")
    reliability_index: float | None = Field(None, description="Fraction of load met by local resources [0-1]")
    strategy: str | None = Field(None, description="Dispatch strategy used")
    estimated_cost: float | None = Field(None, description="Relative dispatch cost (used * LCOE)")

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
    model: str | None = Field(
        None,
        description="Backend model used (random_forest)",
    )

class SolarmanProcessRequest(BaseModel):
    """Request schema to parse Solarman payload and compute PR"""
    payload: dict = Field(..., description="Raw JSON data from Solarman API")
    dc_capacity_kwp: float = Field(..., ge=0, description="Nominal system DC capacity in kWp")
    irradiance_w_m2: float = Field(..., gt=0, description="Plane-of-array solar irradiance in W/m²")
    ambient_temp_c: float | None = Field(None, description="Optional ambient temperature in °C")

class SolarmanProcessResponse(BaseModel):
    """Response schema for Performance Ratio calculations"""
    parsed_data: dict = Field(..., description="Flattened device parameters extracted from payload")
    active_power_kw: float = Field(..., description="Current active power in kW")
    irradiance_w_m2: float = Field(..., description="Irradiance used in W/m²")
    cell_temp_c: float = Field(..., description="Calculated or measured cell temperature in °C")
    expected_power_kw: float = Field(..., description="Expected power output under reference conditions in kW")
    raw_pr: float = Field(..., description="Raw Performance Ratio")
    corrected_pr: float = Field(..., description="Temperature-corrected Performance Ratio")
    temp_derating_factor: float = Field(..., description="Temperature derating factor")

class SolarmanRoiRequest(BaseModel):
    """Request schema for financial calculations"""
    total_generation_kwh: float = Field(..., ge=0, description="Cumulative lifetime generation in kWh")
    initial_investment_kzt: float = Field(..., gt=0, description="CAPEX / Initial investment in KZT")
    tariff_kzt_per_kwh: float = Field(..., gt=0, description="Utility electricity tariff in KZT/kWh")
    opex_annual_kzt: float = Field(0.0, ge=0, description="Annual operational costs in KZT")
    annual_degradation: float = Field(0.005, ge=0, le=0.1, description="Yearly panel degradation rate")
    inflation_rate: float = Field(0.05, ge=-0.1, le=0.3, description="Electricity price annual inflation rate")
    lifetime_years: int = Field(25, ge=1, le=50, description="System expected lifetime in years")

class SolarmanRoiResponse(BaseModel):
    """Response schema for financial calculations"""
    initial_investment_kzt: float = Field(..., description="CAPEX / Initial investment in KZT")
    cumulative_savings_kzt: float = Field(..., description="Projected cumulative savings over system lifetime in KZT")
    net_profit_kzt: float = Field(..., description="Net lifetime profit (savings minus initial CAPEX) in KZT")
    roi_pct: float = Field(..., description="Return on Investment percentage")
    payback_period_years: float = Field(..., description="Calculated payback period in years")
    average_annual_savings_kzt: float = Field(..., description="Average annual savings over system lifetime in KZT")

class SolarmanAlertRequest(BaseModel):
    """Request schema to check system status and send alert"""
    parsed_data: dict = Field(..., description="Parsed Solarman parameters")
    telegram_token: str | None = Field(None, description="Optional Telegram Bot API Token")
    chat_id: str | None = Field(None, description="Optional Telegram Chat ID")

class SolarmanAlertResponse(BaseModel):
    """Response schema for status alerting"""
    is_offline: bool = Field(..., description="True if device is offline")
    is_faulty: bool = Field(..., description="True if faultCode is non-zero")
    alert_sent: bool = Field(..., description="True if Telegram alert was successfully dispatched")
    alert_message: str = Field(..., description="Markdown-formatted warning message")





