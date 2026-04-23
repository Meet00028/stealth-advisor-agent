from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.models import Portfolio

from langfuse.decorators import observe


@dataclass(frozen=True)
class DailyPnlResult:
    day_change_absolute: float
    day_change_percent: float
    total_current_value: float


class PortfolioAnalyticsEngine:
    """I implemented this engine to compute portfolio analytics dynamically from raw holdings."""

    def __init__(
        self,
        portfolio: Portfolio,
        mutual_funds_data: Optional[Dict[str, Dict[str, Any]]] = None,
        sector_mapping: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.portfolio = portfolio
        self.mutual_funds_data = mutual_funds_data or {}
        self.sector_mapping = sector_mapping or {}

    @observe()
    def calculate_daily_pnl(self) -> DailyPnlResult:
        total_current_value = self._total_current_value()
        day_change_absolute = 0.0

        for holding in self.portfolio.holdings.stocks:
            day_change_absolute += float(holding.day_change)

        for holding in self.portfolio.holdings.mutual_funds:
            day_change_absolute += float(holding.day_change)

        day_change_percent = 0.0
        if total_current_value > 0:
            day_change_percent = (day_change_absolute / total_current_value) * 100.0

        return DailyPnlResult(
            day_change_absolute=round(day_change_absolute, 2),
            day_change_percent=round(day_change_percent, 2),
            total_current_value=round(total_current_value, 2),
        )

    def calculate_asset_allocation(self) -> dict[str, float]:
        stocks_value = sum(float(h.current_value) for h in self.portfolio.holdings.stocks)
        mutual_funds_value = sum(float(h.current_value) for h in self.portfolio.holdings.mutual_funds)
        total = stocks_value + mutual_funds_value

        if total <= 0:
            return {"DIRECT_STOCKS": 0.0, "MUTUAL_FUNDS": 0.0}

        return {
            "DIRECT_STOCKS": round((stocks_value / total) * 100.0, 2),
            "MUTUAL_FUNDS": round((mutual_funds_value / total) * 100.0, 2),
        }

    @observe()
    def calculate_sector_allocation(self) -> dict[str, float]:
        total_current_value = self._total_current_value()
        if total_current_value <= 0:
            return {}

        sector_values: dict[str, float] = {}

        for holding in self.portfolio.holdings.stocks:
            sector_values[holding.sector] = sector_values.get(holding.sector, 0.0) + float(holding.current_value)

        for holding in self.portfolio.holdings.mutual_funds:
            allocations = self._mutual_fund_sector_allocation(holding.scheme_code, holding.category)
            if allocations:
                for sector, weight in allocations.items():
                    sector_values[sector] = sector_values.get(sector, 0.0) + (float(holding.current_value) * (weight / 100.0))
            else:
                bucket = self._mutual_fund_fallback_bucket(holding.category)
                sector_values[bucket] = sector_values.get(bucket, 0.0) + float(holding.current_value)

        return {k: round((v / total_current_value) * 100.0, 2) for k, v in sector_values.items()}

    def _total_current_value(self) -> float:
        return sum(float(h.current_value) for h in self.portfolio.holdings.stocks) + sum(
            float(h.current_value) for h in self.portfolio.holdings.mutual_funds
        )

    def _mutual_fund_sector_allocation(self, scheme_code: str, category: str) -> dict[str, float]:
        # Check explicit mappings first
        if category in self.sector_mapping.get("category_to_sector", {}):
            return {self.sector_mapping["category_to_sector"][category]: 100.0}

        mf = self.mutual_funds_data.get(scheme_code)

        if isinstance(mf, dict):
            sector_alloc = mf.get("sector_allocation")
            if isinstance(sector_alloc, dict):
                return {str(k): float(v) for k, v in sector_alloc.items()}

        if category == "SECTORAL_IT":
            return {"INFORMATION_TECHNOLOGY": 100.0}
        if category == "SECTORAL_BANKING":
            return {"BANKING": 100.0}

        return {}

    def _mutual_fund_fallback_bucket(self, category: str) -> str:
        # Load explicit sector mappings if available
        if category in self.sector_mapping.get("category_to_sector", {}):
            return self.sector_mapping["category_to_sector"][category]

        # Use fallback mappings
        if "SECTORAL" in category:
            if "IT" in category or "TECHNOLOGY" in category:
                return "INFORMATION_TECHNOLOGY"
            if "PHARMA" in category or "HEALTHCARE" in category:
                return "HEALTHCARE"
            if "BANK" in category or "FINANCIAL" in category:
                return "BANKING"
            return category.replace("SECTORAL_", "")
        
        return "OTHERS"
