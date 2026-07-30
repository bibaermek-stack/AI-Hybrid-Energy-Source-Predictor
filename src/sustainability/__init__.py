"""
Sustainability metrics — CO₂, LCOE/ROI/payback, and impact narratives.
"""

from src.sustainability.co2_calculator import co2_avoided_kg, trees_equivalent
from src.sustainability.economic_metrics import lcoe, payback_years, roi_percent
from src.sustainability.impact_analyzer import analyze_impact

__all__ = [
    "co2_avoided_kg",
    "trees_equivalent",
    "lcoe",
    "payback_years",
    "roi_percent",
    "analyze_impact",
]
