"""
Natural Language Query API Router.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel
import structlog

from eip.core.models import APIResponse
from eip.core.provider_registry import build_endpoint_meta
from eip.intelligence.nlq_engine import NLQEngine


log = structlog.get_logger()
router = APIRouter()


class NLQRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class NLQResponse(BaseModel):
    selected_intent: str
    answer: str
    sources: list[str]
    source_mode: str


@router.post(
    "/ask",
    response_model=APIResponse[NLQResponse],
    summary="Natural Language Query interface",
)
async def ask_question(request: NLQRequest) -> APIResponse[NLQResponse]:
    """
    Natural Language Query interface.
    
    Accepts plain English questions and returns synthesised answers.
    """
    started_at = perf_counter()
    log.info(
        "nlq_api_request_received",
        question=request.question[:100],
    )

    try:
        engine = NLQEngine()
        result = await engine.answer_question(request.question, request.context)
        
        return APIResponse[NLQResponse](
            success=True,
            data=NLQResponse(
                selected_intent=result["intent"],
                answer=result["answer"],
                sources=result["sources"],
                source_mode=result["source_mode"],
            ),
            error=None,
            meta=build_endpoint_meta(
                pillar="nlq",
                started_at=started_at,
            ),
        )
    except Exception as e:
        log.error("nlq_api_error", error=str(e))
        return APIResponse[NLQResponse](
            success=False,
            data=None,
            error="Failed to process question",
            meta=build_endpoint_meta(
                pillar="nlq",
                started_at=started_at,
            ),
        )
