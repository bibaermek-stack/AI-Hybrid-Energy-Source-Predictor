import logging
import requests
import numpy as np
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SolarmanProcessor:
    """
    Expert utility for parsing Solarman OpenAPI payload, computing Performance Ratio (PR),
    conducting financial/ROI evaluations, calculating environmental equivalents,
    fetching Kazakhstan regional weather forecast, and alerting.
    """

    def __init__(self, dc_capacity_kwp: float, temp_coef: float = -0.004, noct: float = 45.0):
        """
        Initialize the processor.
        
        Args:
            dc_capacity_kwp (float): Nominal DC power rating of the solar array in kWp (P_0).
            temp_coef (float): Temperature coefficient of power (gamma), e.g., -0.004 (-0.4%/°C).
            noct (float): Nominal Operating Cell Temperature in °C.
        """
        self.dc_capacity_kwp = dc_capacity_kwp
        self.temp_coef = temp_coef
        self.noct = noct

    def parse_current_data(self, payload: dict) -> dict:
        """
        Extract variables of interest from Solarman's /device/v1.0/currentData payload.
        
        Args:
            payload (dict): Raw JSON response from Solarman OpenAPI.
            
        Returns:
            dict: Flattened key-value mapping of parameters.
        """
        extracted = {}
        try:
            # Check basic structure
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a dictionary.")
            
            data_list = payload.get("dataList", [])
            for item in data_list:
                key = item.get("key")
                val = item.get("value")
                if key is not None:
                    # Convert values to float/int if possible
                    try:
                        if val is not None:
                            extracted[key] = float(val) if '.' in str(val) or 'e' in str(val).lower() else int(val)
                        else:
                            extracted[key] = None
                    except ValueError:
                        extracted[key] = val  # keep string if parsing fails
                        
            # Extract status flags
            extracted["deviceStatus"] = payload.get("status")
            extracted["deviceId"] = payload.get("deviceId")
            extracted["deviceSn"] = payload.get("deviceSn")
            
        except Exception as e:
            logger.error(f"Error parsing Solarman current data: {e}", exc_info=True)
            raise ValueError(f"Failed to parse Solarman payload: {str(e)}")
            
        return extracted

    def calculate_performance_ratio(self, parsed_data: dict, irradiance_w_m2: float, ambient_temp_c: float | None = None) -> dict:
        """
        Calculate system Performance Ratio (PR) and Temperature-Corrected PR.
        
        Formula:
            PR_raw = P_actual / (P_0 * (G / G_ref))
            where:
                P_actual = Active Power generated (kW)
                P_0 = Nominal DC capacity (kWp)
                G = Solar Irradiance (W/m²)
                G_ref = Standard reference irradiance (1000 W/m²)
            
            T_cell = T_ambient + G * ((NOCT - 20) / 800)  (if cell temp not directly measured)
            PR_corrected = PR_raw / (1 + gamma * (T_cell - 25))
            
        Args:
            parsed_data (dict): Dictionary of extracted parameters from Solarman.
            irradiance_w_m2 (float): Plane-of-array solar irradiance (W/m²). Must be > 0 to avoid division by zero.
            ambient_temp_c (float, optional): Ambient temperature in °C. Required if module temperature is not in payload.
            
        Returns:
            dict: PR metrics.
        """
        if irradiance_w_m2 <= 0:
            raise ValueError("Solar irradiance must be strictly greater than 0 W/m² to calculate PR.")

        try:
            # Solarman active power key is typically 'APo' or 'pac'
            active_power_kw = parsed_data.get("APo", parsed_data.get("pac", 0.0))
            if active_power_kw is None:
                active_power_kw = 0.0

            # Reference irradiance
            g_ref = 1000.0

            # Calculate raw PR
            # Expected power under current irradiance = Nominal Capacity * (G / G_ref)
            expected_power_kw = self.dc_capacity_kwp * (irradiance_w_m2 / g_ref)
            
            if expected_power_kw == 0:
                raw_pr = 0.0
            else:
                raw_pr = active_power_kw / expected_power_kw

            # Determine module/cell temperature
            # Solarman key for radiator/internal temp is often 'T_val', or we estimate from ambient
            cell_temp_c = parsed_data.get("T_val", None)
            
            if cell_temp_c is None:
                if ambient_temp_c is None:
                    # Default cell temp to ambient 25°C estimate if nothing is provided
                    cell_temp_c = 25.0
                else:
                    # Estimate cell temperature using ambient and irradiance
                    cell_temp_c = ambient_temp_c + irradiance_w_m2 * ((self.noct - 20.0) / 800.0)

            # Apply temperature correction coefficient (gamma is negative, e.g. -0.004)
            temp_derating_factor = 1.0 + self.temp_coef * (cell_temp_c - 25.0)
            
            if temp_derating_factor == 0:
                corrected_pr = 0.0
            else:
                corrected_pr = raw_pr / temp_derating_factor

            return {
                "active_power_kw": float(active_power_kw),
                "irradiance_w_m2": irradiance_w_m2,
                "cell_temp_c": float(cell_temp_c),
                "expected_power_kw": expected_power_kw,
                "raw_pr": float(raw_pr),
                "corrected_pr": float(corrected_pr),
                "temp_derating_factor": float(temp_derating_factor)
            }

        except Exception as e:
            logger.error(f"Error calculating Performance Ratio: {e}", exc_info=True)
            raise RuntimeError(f"PR calculation failed: {str(e)}")

    def calculate_roi_metrics(
        self,
        total_generation_kwh: float,
        initial_investment_kzt: float,
        tariff_kzt_per_kwh: float,
        opex_annual_kzt: float = 0.0,
        annual_degradation: float = 0.005,
        inflation_rate: float = 0.05,
        lifetime_years: int = 25
    ) -> dict:
        """
        Conduct financial evaluation including dynamic payback period and ROI.
        
        Args:
            total_generation_kwh (float): Cumulative energy produced (kWh).
            initial_investment_kzt (float): Capital expense (CAPEX) in KZT.
            tariff_kzt_per_kwh (float): Utility tariff rate in KZT/kWh.
            opex_annual_kzt (float): Annual operating cost (KZT).
            annual_degradation (float): Annual loss of system efficiency (e.g. 0.005 = 0.5%/year).
            inflation_rate (float): Annual tariff inflation rate (e.g. 0.05 = 5%).
            lifetime_years (int): Analysis period.
            
        Returns:
            dict: Financial indicators.
        """
        if initial_investment_kzt <= 0:
            raise ValueError("Initial investment must be greater than zero.")

        try:
            # Estimate average annual generation based on current lifetime generation
            # Let's assume total_generation_kwh represents Year 1 equivalent for forecasting
            # Or we can project future cash flows.
            
            # Project cash flows year by year
            cumulative_savings_kzt = 0.0
            cash_flows = []
            payback_year = None
            
            # Baseline Year 1 generation
            yearly_generation = total_generation_kwh
            current_tariff = tariff_kzt_per_kwh

            for year in range(1, lifetime_years + 1):
                # Apply degradation to generation and inflation to tariff
                deg_factor = (1.0 - annual_degradation) ** (year - 1)
                tariff_factor = (1.0 + inflation_rate) ** (year - 1)
                
                annual_revenue = (yearly_generation * deg_factor) * (current_tariff * tariff_factor)
                annual_net_saving = annual_revenue - opex_annual_kzt
                
                cumulative_savings_kzt += annual_net_saving
                cash_flows.append(annual_net_saving)

                # Check for payback period completion
                if cumulative_savings_kzt >= initial_investment_kzt and payback_year is None:
                    # Linear interpolation for fractional year
                    overshoot = cumulative_savings_kzt - initial_investment_kzt
                    fraction = overshoot / annual_net_saving if annual_net_saving > 0 else 0
                    payback_year = float(year) - fraction

            # ROI calculation
            net_profit_kzt = cumulative_savings_kzt - initial_investment_kzt
            roi_pct = (net_profit_kzt / initial_investment_kzt) * 100.0

            return {
                "initial_investment_kzt": initial_investment_kzt,
                "cumulative_savings_kzt": cumulative_savings_kzt,
                "net_profit_kzt": net_profit_kzt,
                "roi_pct": roi_pct,
                "payback_period_years": float(payback_year) if payback_year is not None else float('inf'),
                "average_annual_savings_kzt": cumulative_savings_kzt / lifetime_years
            }

        except Exception as e:
            logger.error(f"Error calculating ROI/Financial metrics: {e}", exc_info=True)
            raise RuntimeError(f"Financial metrics calculation failed: {str(e)}")

    def calculate_environmental_impact(self, co2_offset_metric_tons: float) -> dict:
        """
        Translate cumulative CO2 offset to EPA equivalent environmental values.
        
        Equivalencies (US EPA):
            1 metric ton CO2 = 16.5 mature tree seedlings grown for 10 years
            1 metric ton CO2 = 2558 miles driven by an average gasoline passenger vehicle
            1 metric ton CO2 = 112.5 gallons of gasoline consumed
            
        Args:
            co2_offset_metric_tons (float): CO2 reduction in metric tons.
            
        Returns:
            dict: Environmental equivalence metrics.
        """
        try:
            tree_seedlings = co2_offset_metric_tons * 16.5
            avoided_vehicle_miles = co2_offset_metric_tons * 2558.0
            avoided_gas_gallons = co2_offset_metric_tons * 112.5
            
            return {
                "co2_offset_metric_tons": co2_offset_metric_tons,
                "tree_seedlings_grown_10_years": round(tree_seedlings),
                "avoided_vehicle_miles": avoided_vehicle_miles,
                "avoided_gasoline_gallons": avoided_gas_gallons
            }
        except Exception as e:
            logger.error(f"Error calculating environmental impact: {e}", exc_info=True)
            raise RuntimeError(f"Environmental calculation failed: {str(e)}")

    # Turkistan, Kazakhstan (WeatherAPI.com)
    _WX_LAT = 43.3020
    _WX_LON = 68.2718
    _WX_Q = "43.302,68.2718"

    @staticmethod
    def _weatherapi_key() -> str:
        """WeatherAPI.com key (preferred) or legacy alias."""
        return (
            os.getenv("WEATHERAPI_KEY")
            or os.getenv("WEATHER_API_KEY")
            or ""
        ).strip()

    @staticmethod
    def _estimate_shortwave_wm2(hour_int: int, cloud_pct: float) -> float:
        """Estimate plane irradiance when API has no radiation field."""
        cloud = max(0.0, min(100.0, cloud_pct)) / 100.0
        if 6 <= hour_int <= 18:
            g_clear = np.sin(np.pi * (hour_int - 6.0) / 12.0) * 950.0
            return max(0.0, float(g_clear * (1.0 - 0.75 * cloud)))
        return 0.0

    def fetch_turkistan_weather(self) -> dict:
        """
        Current weather for Turkistan via WeatherAPI.com.

        Env: WEATHERAPI_KEY (required for live data).

        Returns:
            dict: temperature, cloud cover, UV index.
        """
        api_key = self._weatherapi_key()
        if not api_key:
            logger.error("WEATHERAPI_KEY is not set")
            return {
                "location": "Turkistan, Kazakhstan",
                "error": "WEATHERAPI_KEY not configured",
                "latitude": self._WX_LAT,
                "longitude": self._WX_LON,
                "temperature_2m_c": 25.0,
                "cloud_cover_pct": 50,
                "uv_index": 5.0,
                "timestamp": None,
                "source": "fallback",
            }

        url = "https://api.weatherapi.com/v1/current.json"
        params = {
            "key": api_key,
            "q": self._WX_Q,
            "aqi": "no",
        }
        try:
            response = requests.get(url, params=params, timeout=3)
            if response.status_code != 200:
                logger.error(
                    "WeatherAPI current failed: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                response.raise_for_status()
            data = response.json()
            cur = data.get("current") or {}
            loc = data.get("location") or {}
            return {
                "location": f"{loc.get('name', 'Turkistan')}, {loc.get('country', 'Kazakhstan')} (WeatherAPI)",
                "latitude": float(loc.get("lat", self._WX_LAT)),
                "longitude": float(loc.get("lon", self._WX_LON)),
                "temperature_2m_c": float(cur.get("temp_c", 25.0)),
                "cloud_cover_pct": float(cur.get("cloud", 50)),
                "uv_index": float(cur.get("uv", 0.0)),
                "timestamp": cur.get("last_updated"),
                "condition": (cur.get("condition") or {}).get("text"),
                "source": "weatherapi",
            }
        except Exception as e:
            logger.error(f"Failed to fetch WeatherAPI current for Turkistan: {e}", exc_info=True)
            return {
                "location": "Turkistan, Kazakhstan (Fallback)",
                "error": str(e),
                "latitude": self._WX_LAT,
                "longitude": self._WX_LON,
                "temperature_2m_c": 25.0,
                "cloud_cover_pct": 50,
                "uv_index": 5.0,
                "timestamp": None,
                "source": "fallback",
            }

    def fetch_turkistan_hourly_forecast(self) -> dict:
        """
        24h hourly forecast for Turkistan via WeatherAPI.com forecast API.

        Returns:
            dict: {\"forecast\": [ {time, temperature, cloud_cover, shortwave_radiation, uv_index}, ... ]}
        """
        api_key = self._weatherapi_key()
        if not api_key:
            logger.error("WEATHERAPI_KEY is not set for hourly forecast")
            fallback = []
            for h in range(24):
                fallback.append({
                    "time": f"Future Hour {h}",
                    "temperature": 25.0,
                    "cloud_cover": 50.0,
                    "shortwave_radiation": 400.0 if 8 <= h <= 18 else 0.0,
                    "uv_index": 4.0 if 8 <= h <= 18 else 0.0,
                })
            return {"forecast": fallback, "error": "WEATHERAPI_KEY not configured", "source": "fallback"}

        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": api_key,
            "q": self._WX_Q,
            "days": 2,
            "aqi": "no",
            "alerts": "no",
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                logger.error(
                    "WeatherAPI forecast failed: %s %s",
                    response.status_code,
                    response.text[:300],
                )
                response.raise_for_status()
            data = response.json()
            days = (data.get("forecast") or {}).get("forecastday") or []

            records = []
            for day in days:
                for h in day.get("hour") or []:
                    # "2026-07-11 14:00" → ISO-like for sorting/compare
                    t_raw = str(h.get("time") or "")
                    iso_time = t_raw.replace(" ", "T") if " " in t_raw else t_raw
                    temp_val = float(h.get("temp_c", 25.0))
                    cloud_pct = float(h.get("cloud", 50.0))
                    uv_val = float(h.get("uv", 0.0))
                    # Prefer API solar radiation if present (W/m²)
                    rad = h.get("solarradiation")
                    if rad is None:
                        rad = h.get("shortwave_radiation")
                    try:
                        hour_int = int(t_raw.split(" ")[-1].split(":")[0]) if t_raw else 12
                    except (ValueError, IndexError):
                        hour_int = 12
                    if rad is None:
                        g = self._estimate_shortwave_wm2(hour_int, cloud_pct)
                    else:
                        g = max(0.0, float(rad))
                    records.append({
                        "time": iso_time,
                        "temperature": temp_val,
                        "cloud_cover": cloud_pct,
                        "shortwave_radiation": g,
                        "uv_index": uv_val,
                    })

            now_str = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:00")
            future = [r for r in records if r["time"] >= now_str]
            final_records = (future or records)[:24]
            return {"forecast": final_records, "source": "weatherapi"}

        except Exception as e:
            logger.error(f"Failed to fetch WeatherAPI hourly forecast: {e}", exc_info=True)
            fallback = []
            for h in range(24):
                fallback.append({
                    "time": f"Future Hour {h}",
                    "temperature": 25.0,
                    "cloud_cover": 50.0,
                    "shortwave_radiation": 400.0 if 8 <= h <= 18 else 0.0,
                    "uv_index": 4.0 if 8 <= h <= 18 else 0.0,
                })
            return {"forecast": fallback, "error": str(e), "source": "fallback"}

    def check_status_and_alert(
        self,
        parsed_data: dict,
        telegram_token: str | None = None,
        chat_id: str | None = None
    ) -> dict:
        """
        Monitor parsed data for status issues (faultCode, offline). 
        Sends formatted Markdown alert to a Telegram bot.
        
        Args:
            parsed_data (dict): Parsed Solarman parameters.
            telegram_token (str): Telegram Bot API token.
            chat_id (str): Telegram Chat ID.
            
        Returns:
            dict: Alert execution status.
        """
        device_id = parsed_data.get("deviceId", "Unknown ID")
        device_sn = parsed_data.get("deviceSn", "Unknown SN")
        fault_code = parsed_data.get("faultCode", 0)
        device_status = parsed_data.get("deviceStatus", "unknown")
        
        # Check if offline or faulty
        is_offline = (device_status == 0 or str(device_status) == "0" or str(device_status).lower() == "offline")
        is_faulty = (fault_code is not None and int(fault_code) > 0)
        
        alert_sent = False
        alert_message = ""
        
        if is_offline or is_faulty:
            alert_message = f"🚨 *Solarman Alert: Device Issue Detected!*\n\n"
            alert_message += f"• *Device ID:* `{device_id}`\n"
            alert_message += f"• *Serial Number:* `{device_sn}`\n"
            
            if is_offline:
                alert_message += f"• *Status:* 🔴 `OFFLINE` (Status code: {device_status})\n"
            if is_faulty:
                alert_message += f"• *Fault Code:* ⚠️ `{fault_code}`\n"
                
            alert_message += f"• *Timestamp (UTC):* `{datetime.now(timezone.utc).isoformat()}`"
            
            if telegram_token and chat_id:
                url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": alert_message,
                    "parse_mode": "Markdown"
                }
                try:
                    res = requests.post(url, json=payload, timeout=10)
                    res.raise_for_status()
                    alert_sent = True
                except Exception as e:
                    logger.error(f"Failed to send Telegram alert: {e}", exc_info=True)
            else:
                logger.warning("Telegram configuration missing. Alert logged to console instead.")
                
        return {
            "is_offline": is_offline,
            "is_faulty": is_faulty,
            "alert_sent": alert_sent,
            "alert_message": alert_message
        }
