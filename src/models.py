from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class NewsEntities(BaseModel):
    """I built this model to capture the specific entities mentioned in a news article."""
    sectors: List[str] = Field(default_factory=list)
    stocks: List[str] = Field(default_factory=list)
    indices: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

class NewsArticle(BaseModel):
    """I implemented this model to represent a single news article with its sentiment, causal factors, and conflict flags."""
    id: str
    headline: str
    summary: str
    published_at: str
    source: str
    sentiment: str
    sentiment_score: float
    scope: str
    impact_level: str
    entities: NewsEntities
    causal_factors: List[str] = Field(default_factory=list)
    conflict_flag: bool = False
    conflict_explanation: Optional[str] = None

class IndexData(BaseModel):
    """I created this model to track market index performance, including high/lows and absolute changes."""
    symbol: str = Field(description="The dictionary key from the JSON")
    name: str
    current_value: float
    previous_close: float
    change_percent: float
    change_absolute: float
    day_high: float
    day_low: float
    high_52_week: float = Field(alias="52_week_high")
    low_52_week: float = Field(alias="52_week_low")
    sentiment: str

class SectorPerformance(BaseModel):
    """I built this model to represent the daily performance of a specific sector and its key drivers."""
    sector_name: str = Field(description="The dictionary key from the JSON")
    change_percent: float
    sentiment: str
    key_drivers: List[str] = Field(default_factory=list)
    top_gainers: List[str] = Field(default_factory=list)
    top_losers: List[str] = Field(default_factory=list)

class StockData(BaseModel):
    """I implemented this model to track individual stock metrics like beta, market cap, and PE ratio."""
    ticker: str = Field(description="The dictionary key from the JSON")
    name: str
    sector: str
    sub_sector: str
    current_price: float
    previous_close: float
    change_percent: float
    change_absolute: float
    volume: int
    avg_volume_20d: int
    market_cap_cr: int
    pe_ratio: float
    high_52_week: float = Field(alias="52_week_high")
    low_52_week: float = Field(alias="52_week_low")
    beta: float


class StockHolding(BaseModel):
    """I implemented this model to represent a single direct stock position inside a portfolio."""
    symbol: str
    name: str
    sector: str
    quantity: int
    avg_buy_price: float
    current_price: float
    investment_value: float
    current_value: float
    gain_loss: float
    gain_loss_percent: float
    day_change: float
    day_change_percent: float
    weight_in_portfolio: float


class MutualFundHolding(BaseModel):
    """I implemented this model to represent a mutual fund position inside a portfolio."""
    scheme_code: str
    scheme_name: str
    category: str
    amc: str
    units: float
    avg_nav: float
    current_nav: Optional[float] = None
    current_price: Optional[float] = None
    investment_value: float
    current_value: float
    gain_loss: float
    gain_loss_percent: float
    day_change: float
    day_change_percent: float
    weight_in_portfolio: float
    top_holdings: List[str] = Field(default_factory=list)


class PortfolioHoldings(BaseModel):
    """I implemented this model to capture all holdings inside a portfolio."""
    stocks: List[StockHolding] = Field(default_factory=list)
    mutual_funds: List[MutualFundHolding] = Field(default_factory=list)


class Portfolio(BaseModel):
    """I implemented this model to represent an investor portfolio with raw holdings and metadata."""
    portfolio_id: str = Field(description="The dictionary key from the JSON")
    user_id: str
    user_name: str
    portfolio_type: str
    risk_profile: str
    investment_horizon: str
    description: str
    total_investment: float
    current_value: float
    overall_gain_loss: float
    overall_gain_loss_percent: float
    holdings: PortfolioHoldings
    analytics: Optional[Dict[str, Any]] = None


class CausalDriver(BaseModel):
    """I implemented this model to capture a single causal chain from macro news to portfolio impact."""
    macro_event: str = ""
    sector: str = ""
    stock: str = ""
    portfolio_impact: str = ""


class ConflictResolution(BaseModel):
    stock: str = ""
    explanation: str = ""


class AgentBriefing(BaseModel):
    """I implemented this model to represent the final structured output produced by the reasoning agent."""
    executive_summary: str
    causal_links: List[CausalDriver] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    conflicts_resolved: List[ConflictResolution] = Field(default_factory=list)
    risk_warnings: Optional[str] = None


class EvaluationResult(BaseModel):
    """I implemented this model to represent an LLM-based evaluation of the agent's reasoning quality."""
    reasoning_score: int = Field(default=3, ge=1, le=5)
    factual_inconsistencies: List[str] = Field(default_factory=list)
    feedback: str
