"""
SafeNet AI — Number Checker API (Module F)

POST /api/check-number
  Body: { phone_number: str, pasted_text?: str }
  Returns: NumberRiskResult serialised as JSON
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.number_checker.checker import check_number, NumberRiskResult

router = APIRouter(tags=["number_checker"])


class CheckNumberRequest(BaseModel):
    phone_number: str = Field(
        ...,
        description="The phone number to check (any format, e.g. +91XXXXXXXXXX)",
        examples=["+916511361582"],
    )
    pasted_text: Optional[str] = Field(
        None,
        description=(
            "Optional: paste the SMS message or call transcript text you received. "
            "This is analysed for scam-language patterns."
        ),
        examples=["Your account will be frozen. Call immediately to avoid legal action."],
    )


class CheckNumberResponse(BaseModel):
    phone_number:    str
    risk_level:      str          # low | medium | high | critical
    confidence:      float        # 0.0 – 1.0
    reasons:         list[str]    # specific, traceable reasons
    recommendation:  str
    text_score:      Optional[int]  = None
    sources_checked: list[str]      = []
    graph_case_id:   Optional[str]  = None
    graph_risk_score: Optional[float] = None
    graph_primary_threat: Optional[str] = None


@router.post(
    "/check-number",
    response_model=CheckNumberResponse,
    summary="Check a phone number for fraud risk",
    description=(
        "Queries the fraud graph, runs scam-pattern analysis on any pasted text, "
        "and checks the number against a synthetic blocklist. Returns an explainable "
        "risk verdict with specific reasons for every flag raised. "
        "⚠️ SYNTHETIC DATA — no real call interception."
    ),
)
def check_number_endpoint(body: CheckNumberRequest) -> CheckNumberResponse:
    result: NumberRiskResult = check_number(
        phone_number=body.phone_number,
        pasted_text=body.pasted_text or None,
    )

    graph_case_id      = None
    graph_risk_score   = None
    graph_primary_threat = None

    if result.graph_case:
        graph_case_id        = result.graph_case.get("caseId")
        graph_risk_score     = result.graph_case.get("riskScore")
        graph_primary_threat = result.graph_case.get("primaryThreat")

    return CheckNumberResponse(
        phone_number=body.phone_number,
        risk_level=result.risk_level,
        confidence=result.confidence,
        reasons=result.reasons,
        recommendation=result.recommendation,
        text_score=result.text_score,
        sources_checked=result.sources_checked,
        graph_case_id=graph_case_id,
        graph_risk_score=graph_risk_score,
        graph_primary_threat=graph_primary_threat,
    )
