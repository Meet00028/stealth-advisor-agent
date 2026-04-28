from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langfuse.callback import CallbackHandler

from src.analytics.engine import DailyPnlResult
from src.models import AgentBriefing, NewsArticle, Portfolio

# 1. Force Langfuse to print EVERYTHING to the terminal 
# os.environ["LANGFUSE_DEBUG"] = "True" 
# logging.getLogger("langfuse").setLevel(logging.DEBUG) 

# 1. Force load the environment variables right here in the agent file 
load_dotenv()

from langfuse.decorators import observe
from langfuse.callback import CallbackHandler

try:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.prompts import ChatPromptTemplate
except Exception:
    BaseChatModel = object
    ChatPromptTemplate = None


class FinancialAdvisorAgent:
    """I built this reasoning engine to generate causal, user-facing portfolio briefings using an LLM."""

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

    @observe()
    def generate_briefing(
        self,
        portfolio: Portfolio,
        daily_pnl: DailyPnlResult,
        sector_allocation: dict[str, float],
        risk_warnings: Optional[str],
        macro_sentiment: str,
        relevant_news: List[NewsArticle],
        sector_trends: Optional[dict[str, dict[str, Any]]] = None,
        stock_sector_divergences: Optional[list[dict[str, Any]]] = None,
    ) -> AgentBriefing:
        if ChatPromptTemplate is None:
            raise RuntimeError(
                "I could not import langchain_core. Please install LangChain to use FinancialAdvisorAgent."
            )

        system_prompt = (
            "You are an autonomous financial advisor agent.\n"
            "You must speak directly to the user in second-person (e.g., 'Your portfolio fell because...').\n"
            "Your primary job is causal reasoning, not summarization.\n\n"
            "Required reasoning behavior:\n"
            "1) Perform causal linking: Macro/market news -> sector impact -> specific holdings -> portfolio impact.\n"
            "2) Be explicit and numeric when possible, referencing sector weights, daily % moves, and P&L.\n"
            "3) Resolve conflicts: If an article is stock-specific and positive/negative but the stock moved opposite,\n"
            "   explain the contradiction using broader market/sector forces.\n"
            "4) Prioritize high-impact signals over noise. Use only MEDIUM/HIGH impact news provided.\n"
            "5) Provide a Confidence Score (0.0 to 1.0) indicating how confident you are in these causal links.\n\n"
            "Output rules:\n"
            "- Return a JSON that matches the provided schema exactly.\n"
            "- executive_summary must be exactly 2 sentences.\n"
            "- populate 'causal_links' with the macro->sector->stock chain using keys: macro_event, sector, stock, portfolio_impact.\n"
            "- If Stock vs Sector divergences are provided, mention each of them in conflicts_resolved using keys: stock, explanation.\n"
        )

        human_prompt = (
            "Portfolio context (JSON):\n{portfolio_json}\n\n"
            "Daily P&L (JSON):\n{daily_pnl_json}\n\n"
            "Sector allocation (percent weights, JSON):\n{sector_allocation_json}\n\n"
            "Sector trends (JSON):\n{sector_trends_json}\n\n"
            "Stock vs sector divergences (JSON):\n{stock_sector_divergences_json}\n\n"
            "Macro sentiment:\n{macro_sentiment}\n\n"
            "Risk warnings (optional):\n{risk_warnings}\n\n"
            "Relevant news (JSON list):\n{news_json}\n\n"
            "Generate the final briefing now.\n"
            "{format_instructions}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", human_prompt),
            ]
        )

        inputs = {
            "portfolio_json": self._to_pretty_json(self._safe_dump(portfolio)),
            "daily_pnl_json": self._to_pretty_json(
                {
                    "day_change_absolute": daily_pnl.day_change_absolute,
                    "day_change_percent": daily_pnl.day_change_percent,
                    "total_current_value": daily_pnl.total_current_value,
                }
            ),
            "sector_allocation_json": self._to_pretty_json(sector_allocation),
            "sector_trends_json": self._to_pretty_json(sector_trends or {}),
            "stock_sector_divergences_json": self._to_pretty_json(stock_sector_divergences or []),
            "macro_sentiment": macro_sentiment,
            "risk_warnings": risk_warnings or "",
            "news_json": self._to_pretty_json([self._safe_dump(a) for a in relevant_news]),
            "format_instructions": "", # Will be populated if fallback is used
        }

        config = {}
        handler = None
        if CallbackHandler is not None:
            handler = CallbackHandler() 
            config = {"callbacks" : [handler]} 

        with_structured_output = getattr(self.llm, "with_structured_output", None)
        if callable(with_structured_output):
            structured_llm = with_structured_output(AgentBriefing)
            chain = prompt | structured_llm
            
            # 1. Run the LLM
            result = chain.invoke(inputs, config=config)
            
            # 2. FORCE the trace to upload before returning!
            if handler is not None:
                handler.flush() 
                
            # 3. Now return the data to the user
            return self._coerce_briefing(result)

        try:
            from langchain_core.output_parsers import PydanticOutputParser
        except Exception as exc:
            raise RuntimeError(
                "I could not bind structured output because langchain_core.output_parsers is unavailable."
            ) from exc

        parser = PydanticOutputParser(pydantic_object=AgentBriefing)
        inputs["format_instructions"] = parser.get_format_instructions()
        chain = prompt | self.llm | parser
        
        result = chain.invoke(inputs, config=config)
        if handler is not None:
            handler.flush()
        return self._coerce_briefing(result)

    def _safe_dump(self, obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return obj

    def _coerce_briefing(self, value: Any) -> AgentBriefing:
        if isinstance(value, AgentBriefing):
            return value
        if isinstance(value, dict):
            normalized = dict(value)
            causal_links = normalized.get("causal_links")
            if isinstance(causal_links, dict):
                normalized["causal_links"] = [causal_links]
            elif causal_links is None:
                normalized["causal_links"] = []

            conflicts_resolved = normalized.get("conflicts_resolved")
            if isinstance(conflicts_resolved, dict):
                normalized["conflicts_resolved"] = [conflicts_resolved] if conflicts_resolved else []
            elif conflicts_resolved is None:
                normalized["conflicts_resolved"] = []

            return AgentBriefing(**normalized)
        if hasattr(value, "model_dump"):
            return AgentBriefing(**value.model_dump())
        if hasattr(value, "dict"):
            return AgentBriefing(**value.dict())
        return AgentBriefing(executive_summary=str(value))

    def _to_pretty_json(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
