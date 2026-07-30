"""
Reusable metric / energy cards.

Delegates to the premium ui_kit so multipage shells and legacy imports stay stable.
"""

from __future__ import annotations

from dashboard.components.ui_kit import display_energy_metrics, metric_card

# Legacy name used by older pages
energy_metric_card = metric_card

__all__ = ["energy_metric_card", "display_energy_metrics", "metric_card"]
