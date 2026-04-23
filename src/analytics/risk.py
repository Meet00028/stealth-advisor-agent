from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.models import Portfolio

from langfuse.decorators import observe


class RiskDetector:
    """I implemented this module to flag portfolio concentration risks based on sector allocation."""

    def detect_concentration_risk(self, sector_allocation: dict[str, float]) -> dict[str, Any]:
        flagged_sectors: dict[str, float] = {
            sector: weight for sector, weight in sector_allocation.items() if weight > 40.0
        }
        if not flagged_sectors:
            return {"has_risk": False, "flagged_sectors": {}, "warning": None}
        return {
            "has_risk": True,
            "flagged_sectors": flagged_sectors,
            "warning": "CRITICAL: High concentration risk detected in one or more sectors.",
        }


