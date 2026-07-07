"""
SafeNet AI — Citizen Shield: FastAPI Router

Exposes:
  POST /shield/ask   — conversational agent endpoint

Module contract (safenet.md §3):
  Route handler is a thin wrapper around agent.ask().
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.citizen_shield.agent import ask, SUPPORTED_LANGUAGES

router = APIRouter(prefix="/shield", tags=["Citizen Shield"])


class AskRequest(BaseModel):
    """Request body for POST /shield/ask."""
    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., min_length=1, max_length=2000,
                       description="User's natural-language question.")
    language: str = Field(
        default="en",
        description=(
            f"Response language code. Supported: "
            f"{', '.join(SUPPORTED_LANGUAGES.keys())}. "
            "Defaults to 'en' (English)."
        ),
    )


class AskResponse(BaseModel):
    """Response schema — must match the chat widget's expected shape."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    sender: str
    text: str
    timestamp: str
    isActionable: bool
    intent: str
    risk_level: str
    language: str


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the Citizen Shield fraud-prevention agent",
)
async def ask_endpoint(body: AskRequest) -> AskResponse:
    """
    Accepts a natural-language question and returns a structured response.

    Intent routing:
      suspicious_call       — scores the call description with Module A's classifier
      upi_fraud_check       — checks UPI IDs against the blocklist and fraud patterns
      counterfeit_note_query — retrieves currency verification guidance
      general_question      — broad semantic search over the knowledge base

    Language support:
      English always available. Hindi (and others) when LLM_API_KEY is set.
      Falls back to English + note when translation is unavailable.

    Args:
        body.query:    User message.
        body.language: Response language code (default 'en').

    Returns:
        AskResponse matching the CitizenShieldChat widget schema.
    """
    language = body.language if body.language in SUPPORTED_LANGUAGES else "en"
    result = ask(body.query, language=language)
    return AskResponse(**result)
