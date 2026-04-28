from __future__ import annotations

import json
from typing import Any

from src.models import AgentBriefing, EvaluationResult

from langfuse.decorators import observe
from langfuse.callback import CallbackHandler

try:
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.prompts import ChatPromptTemplate
except Exception:
    BaseChatModel = object
    ChatPromptTemplate = None


class SelfEvaluator:
    """I built this self-evaluation layer to grade the agent's causal reasoning quality using an LLM judge."""

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

    @observe()
    def evaluate_briefing(self, briefing: AgentBriefing, portfolio_id: str) -> EvaluationResult:
        if ChatPromptTemplate is None:
            raise RuntimeError("I could not import langchain_core. Please install LangChain to use SelfEvaluator.")

        system_prompt = (
            "You are a strict evaluator for an autonomous financial advisor agent.\n"
            "Grade the provided briefing on a scale of 1-5 on how well it explains the 'Why' behind the portfolio move.\n"
            "Your score must reflect whether the briefing explicitly links:\n"
            "Macro news -> sector trends -> specific holdings -> portfolio-level impact.\n\n"
            "Scoring rubric (1-5):\n"
            "- 5: Excellent causal chains with numeric grounding, plus conflicts resolved clearly.\n"
            "- 4: Good causal chain and some numeric grounding, limited conflict coverage.\n"
            "- 3: Moderate explanation but misses some key 'Why' factors.\n"
            "- 2: Mostly summary with weak causality; minimal numeric grounding.\n"
            "- 1: No causal linking; generic statements.\n\n"
            "Additionally, you MUST flag any factual inconsistencies between the P&L data and the explanation.\n"
            "Output must match the provided schema exactly.\n"
        )

        human_prompt = (
            "Portfolio ID:\n{portfolio_id}\n\n"
            "Agent briefing JSON:\n{briefing_json}\n\n"
            "Return the evaluation now.\n"
            "{format_instructions}"
        )

        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", human_prompt)])

        inputs = {
            "portfolio_id": portfolio_id,
            "briefing_json": self._to_pretty_json(self._safe_dump(briefing)),
            "format_instructions": "", # Will be populated if fallback is used
        }

        config = {}
        handler = None
        if CallbackHandler is not None:
            handler = CallbackHandler()
            config["callbacks"] = [handler]

        with_structured_output = getattr(self.llm, "with_structured_output", None)
        if callable(with_structured_output):
            structured_llm = with_structured_output(EvaluationResult)
            chain = prompt | structured_llm
            
            # 1. Run the LLM
            result = chain.invoke(inputs, config=config)
            
            # 2. FORCE the trace to upload before returning!
            if handler is not None:
                handler.flush() 
                
            # 3. Now return the data to the user
            return self._coerce_evaluation(result)

        try:
            from langchain_core.output_parsers import PydanticOutputParser
        except Exception as exc:
            raise RuntimeError(
                "I could not bind structured output because langchain_core.output_parsers is unavailable."
            ) from exc

        parser = PydanticOutputParser(pydantic_object=EvaluationResult)
        inputs["format_instructions"] = parser.get_format_instructions()
        chain = prompt | self.llm | parser
        
        result = chain.invoke(inputs, config=config)
        if handler is not None:
            handler.flush()
        return self._coerce_evaluation(result)

    def _safe_dump(self, obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return obj

    def _to_pretty_json(self, obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)

    def _coerce_evaluation(self, value: Any) -> EvaluationResult:
        if isinstance(value, EvaluationResult):
            return value
        if isinstance(value, dict):
            return EvaluationResult(**value)
        if hasattr(value, "model_dump"):
            return EvaluationResult(**value.model_dump())
        if hasattr(value, "dict"):
            return EvaluationResult(**value.dict())
        return EvaluationResult(feedback=str(value))
