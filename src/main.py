from langfuse.decorators import observe, langfuse_context
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException

from src.agents.advisor import FinancialAdvisorAgent
from src.analytics.engine import PortfolioAnalyticsEngine
from src.analytics.risk import RiskDetector
from src.utils.data_loader import DataLoader
from src.agents.evaluator import SelfEvaluator
from src.intelligence.processor import NewsProcessor
from src.intelligence.trends import TrendAnalyzer

try:
    from langchain_core.language_models.chat_models import BaseChatModel
except Exception:
    BaseChatModel = object


def _create_llm(model_type: str = "generator") -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from environment variables.")
        # Decoupled Evaluator LLM vs Agent LLM logic
        model_name = "gemini-1.5-pro" if model_type == "evaluator" else "gemini-1.5-flash"
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.0 if model_type == "evaluator" else 0.2
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing from environment variables.")
        # Decoupled Evaluator LLM vs Agent LLM logic
        model_name = "gpt-4o" if model_type == "evaluator" else "gpt-4o-mini"
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0.0 if model_type == "evaluator" else 0.2
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


try:
    from langfuse import Langfuse
    langfuse_client = Langfuse()
    langfuse_client.auth_check()
except Exception as e:
    print(f"WARNING: Langfuse initialization failed: {e}")

app = FastAPI(title="Autonomous Financial Advisor Agent")


@app.get("/api/v1/analyze_portfolio/{portfolio_id}")
@observe()
def analyze_portfolio(portfolio_id: str) -> Dict[str, Any]:
    
    loader = DataLoader()
    portfolio = loader.get_portfolio(portfolio_id)
    
    # Langfuse Best Practice: Attach User/Session/Feature tags to the Root Trace
    langfuse_context.update_current_trace(
        name="analyze_portfolio_request",
        user_id=portfolio.user_id,
        session_id=portfolio_id,
        tags=[portfolio.portfolio_type, portfolio.risk_profile, "financial_advisor_agent"]
    )

    mutual_funds_data = loader.get_mutual_funds()

    news_processor = NewsProcessor(loader)
    trend_analyzer = TrendAnalyzer(loader)
    macro_sentiment = trend_analyzer.get_macro_sentiment()
    sector_performance = loader.get_sector_performance()

    target_sectors = sorted({h.sector for h in portfolio.holdings.stocks})
    target_stocks = sorted({h.symbol for h in portfolio.holdings.stocks})
    for mf in portfolio.holdings.mutual_funds:
        for t in mf.top_holdings:
            target_stocks.append(t)
    target_stocks = sorted(set(target_stocks))

    relevant_news = news_processor.filter_relevant_news(target_sectors=target_sectors, target_stocks=target_stocks)
    sector_trends: Dict[str, Dict[str, Any]] = {}
    for sector in target_sectors:
        perf = sector_performance.get(sector)
        if perf is not None:
            sector_trends[sector] = {
                "change_percent": perf.change_percent,
                "sentiment": perf.sentiment,
                "key_drivers": perf.key_drivers,
            }

    stock_sector_divergences: list[dict[str, Any]] = []
    for holding in portfolio.holdings.stocks:
        perf = sector_performance.get(holding.sector)
        if perf is None:
            continue
        sector_change = float(perf.change_percent)
        stock_change = float(holding.day_change_percent)
        if (sector_change > 0 and stock_change < 0) or (sector_change < 0 and stock_change > 0):
            stock_sector_divergences.append(
                {
                    "symbol": holding.symbol,
                    "sector": holding.sector,
                    "stock_change_percent": stock_change,
                    "sector_change_percent": sector_change,
                }
            )

    engine = PortfolioAnalyticsEngine(
        portfolio=portfolio, 
        mutual_funds_data=mutual_funds_data,
        sector_mapping=loader.get_sector_mapping(),
    )
    daily_pnl = engine.calculate_daily_pnl()
    asset_allocation = engine.calculate_asset_allocation()
    sector_allocation = engine.calculate_sector_allocation()

    risk_detector = RiskDetector()
    concentration_risk = risk_detector.detect_concentration_risk(sector_allocation)
    risk_warnings: Optional[str] = concentration_risk.get("warning")

    try:
        llm = _create_llm()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    print(">>> STARTING AGENT GENERATION...")
    advisor = FinancialAdvisorAgent(llm=llm)
    briefing = advisor.generate_briefing(
        portfolio=portfolio,
        daily_pnl=daily_pnl,
        sector_allocation=sector_allocation,
        risk_warnings=risk_warnings,
        macro_sentiment=macro_sentiment,
        relevant_news=relevant_news,
        sector_trends=sector_trends,
        stock_sector_divergences=stock_sector_divergences,
    )

    try:
        evaluator_llm = _create_llm(model_type="evaluator")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    print(">>> STARTING EVALUATION...")
    evaluator = SelfEvaluator(llm=evaluator_llm)
    evaluation = evaluator.evaluate_briefing(briefing=briefing, portfolio_id=portfolio_id)

    print(">>> FLUSHING LANGFUSE...")
    # Flush using the context object 
    langfuse_context.flush()
    
    print(">>> RETURNING JSON!")

    return {
        "portfolio_id": portfolio_id,
        "analytics": {
            "daily_pnl": {
                "day_change_absolute": daily_pnl.day_change_absolute,
                "day_change_percent": daily_pnl.day_change_percent,
                "total_current_value": daily_pnl.total_current_value,
            },
            "asset_allocation": asset_allocation,
            "sector_allocation": sector_allocation,
            "sector_trends": sector_trends,
            "stock_sector_divergences": stock_sector_divergences,
            "risk": concentration_risk,
        },
        "briefing": briefing.model_dump() if hasattr(briefing, "model_dump") else (briefing.dict() if hasattr(briefing, "dict") else briefing),
        "evaluation": evaluation.model_dump() if hasattr(evaluation, "model_dump") else (evaluation.dict() if hasattr(evaluation, "dict") else evaluation),
    }
