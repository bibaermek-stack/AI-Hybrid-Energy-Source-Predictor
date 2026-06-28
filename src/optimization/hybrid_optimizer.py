import joblib
import numpy as np
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

ARTIFACT_PATH = Path(os.getenv("MODEL_PATH", "artifacts")).resolve()

# Models are loaded by api/routes.py, not here
# This ensures single source of truth


def optimize_energy(solar, wind):
    """
    Optimize energy recommendation based on solar and wind output.
    
    Args:
        solar (float): Solar power output in kW
        wind (float): Wind power output in kW
    
    Returns:
        dict: Energy metrics and recommendation
        
    Raises:
        ValueError: If inputs are invalid
    """
    # Validate input types
    if not isinstance(solar, (int, float)) or not isinstance(wind, (int, float)):
        raise ValueError(f"Solar and wind must be numeric values, got {type(solar)} and {type(wind)}")
    
    # Validate input ranges
    if solar < 0 or wind < 0:
        raise ValueError(f"Energy values cannot be negative: solar={solar}, wind={wind}")
    
    # Validate for NaN and Inf
    if np.isnan(solar) or np.isnan(wind) or np.isinf(solar) or np.isinf(wind):
        raise ValueError(f"Energy values contain NaN or Inf: solar={solar}, wind={wind}")

    total = solar + wind

    # Choose based on higher output
    if solar > wind:
        best = "Solar"
    else:
        best = "Wind"

    return {
        "solar_power": float(solar),
        "wind_power": float(wind),
        "total_energy": float(total),
        "recommended_source": best
    }


if __name__ == "__main__":
    # Example usage for testing
    test_result = optimize_energy(800.5, 600.3)
    print(test_result)