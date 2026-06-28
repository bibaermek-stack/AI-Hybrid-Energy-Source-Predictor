import json
from datetime import datetime, timezone
from pathlib import Path

class PredictionLogger:
    """Log predictions for monitoring and debugging"""
    
    def __init__(self, log_path="logs/predictions.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(exist_ok=True)
    
    def log_prediction(self, inputs: dict, solar: float, wind: float, recommendation: str):
        """
        Log a prediction with inputs and outputs
        
        Args:
            inputs: Dictionary of input features
            solar: Solar power prediction
            wind: Wind power prediction
            recommendation: Recommended source
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs": inputs,
            "outputs": {
                "solar": float(solar),
                "wind": float(wind),
                "recommendation": recommendation
            }
        }
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            pass
