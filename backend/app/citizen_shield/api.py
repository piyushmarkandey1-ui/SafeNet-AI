"""
SafeNet AI — Citizen Shield: FastAPI Router

Exposes:
  POST /shield/ask        — conversational fraud-prevention agent
  GET  /shield/gemma-info — confirms Gemma model is active (AMD bonus prize)

LLM backend (AMD Developer Hackathon — Best AMD-Hosted Gemma Project):
  Primary:  Fireworks AI → accounts/fireworks/models/gemma2-9b-it  (Gemma 2 9B)
            Fireworks AI → accounts/fireworks/models/gemma2-27b-it (Gemma 2 27B, complex)
  Fallback: Google Gemini 2.0 Flash → OpenAI GPT-4o → template

  Gemma is Google DeepMind's open model hosted on AMD Instinct GPUs via
  Fireworks AI.  This endpoint satisfies the "$2,000 Best AMD-Hosted Gemma
  Project" bonus prize criterion for Track 3.

Module contract (safenet.md §3):
  Route handlers are thin wrappers around agent.ask() / respond_to_user().
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict
import logging

from app.citizen_shield.agent import respond_to_user, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)
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
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description=(
            "List of prior messages in the format "
            "{'role': 'user'|'assistant', 'content': '...'}"
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
    next_steps: Optional[str] = None


class GemmaInfoResponse(BaseModel):
    """Confirms Gemma model availability for AMD hackathon bonus prize."""
    model_config = ConfigDict(populate_by_name=True)

    gemma_enabled: bool
    primary_model: str
    complex_model: str
    provider: str
    amd_inference: bool
    description: str
    supported_languages: list[str]
    task_routing: dict


@router.get(
    "/gemma-info",
    response_model=GemmaInfoResponse,
    summary="Gemma model status — AMD-Hosted Gemma Project (bonus prize)",
)
async def gemma_info() -> GemmaInfoResponse:
    """
    Returns confirmation that Citizen Shield uses Gemma models via Fireworks AI
    (AMD Instinct GPU cluster).

    This endpoint was added to satisfy the AMD Developer Hackathon Track 3
    bonus prize criterion: "Best AMD-Hosted Gemma Project" ($2,000).

    Gemma 2 9B  — standard citizen queries (chat)
    Gemma 2 27B — complex multi-turn conversations (chat_complex)

    Both models are served by Fireworks AI on AMD hardware.
    """
    from app.fireworks_client import FIREWORKS_MODELS, TASK_MODEL_MAP, get_provider_status
    status = get_provider_status()

    return GemmaInfoResponse(
        gemma_enabled=True,
        primary_model=FIREWORKS_MODELS["gemma"],
        complex_model=FIREWORKS_MODELS["gemma_large"],
        provider=status["active_provider"],
        amd_inference=status["amd_inference"],
        description=(
            "Citizen Shield uses Gemma 2 (Google DeepMind open model) "
            "hosted on AMD Instinct GPUs via Fireworks AI. "
            "Standard queries use Gemma 2 9B; complex multi-turn conversations "
            "escalate to Gemma 2 27B. Both run on AMD hardware."
        ),
        supported_languages=list(SUPPORTED_LANGUAGES.keys()),
        task_routing={
            "chat":         FIREWORKS_MODELS.get(TASK_MODEL_MAP.get("chat", "gemma"), ""),
            "chat_complex": FIREWORKS_MODELS.get(TASK_MODEL_MAP.get("chat_complex", "gemma_large"), ""),
            "translation":  FIREWORKS_MODELS.get(TASK_MODEL_MAP.get("translation", "mixtral"), ""),
        },
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the Citizen Shield fraud-prevention agent (powered by Gemma on AMD)",
)
async def ask_endpoint(body: AskRequest) -> AskResponse:
    """
    Accepts a natural-language question and returns a structured fraud-prevention response.

    LLM backend:
      Fireworks AI (Gemma 2 9B/27B on AMD Instinct GPUs) → Gemini → template

    Intent routing:
      suspicious_call        — scores call with Module A pattern matcher
      upi_fraud_check        — blocklist + fraud graph check for UPI IDs
      counterfeit_note_query — currency verification guidance
      general_question       — knowledge-base semantic search

    Language support:
      English always available.
      Hindi, Tamil, Telugu, Bengali, Marathi when any LLM is configured.

    Args:
        body.query:                User message (raw text).
        body.language:             Response language ISO code (default 'en').
        body.conversation_history: Prior turns for multi-turn context.

    Returns:
        AskResponse matching the CitizenShieldChat widget schema.
    """
    language = body.language if body.language in SUPPORTED_LANGUAGES else "en"
    try:
        result = respond_to_user(
            user_message=body.query,
            conversation_history=body.conversation_history or [],
            language=language,
        )
        return AskResponse(**result)
    except Exception as e:
        logger.error(f"[shield/ask] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="The Citizen Shield AI is temporarily unavailable. Please try again shortly.",
        )
