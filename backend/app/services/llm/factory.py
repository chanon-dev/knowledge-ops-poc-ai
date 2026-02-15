"""LLM client factory - creates the right client based on provider configuration."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.ai_provider import AIProvider
from app.models.allowed_model import AllowedModel
from app.services.llm.ollama_client import OllamaClient
from app.services.llm.openai_client import OpenAICompatibleClient

logger = logging.getLogger(__name__)


async def get_llm_client(
    model_name: str,
    tenant_id: UUID,
    db: AsyncSession,
) -> OllamaClient | OpenAICompatibleClient:
    """Look up provider for a model and return the appropriate LLM client.

    Falls back to Ollama if no provider is configured.
    """
    result = await db.execute(
        select(AllowedModel)
        .options(joinedload(AllowedModel.provider))
        .where(
            AllowedModel.tenant_id == tenant_id,
            AllowedModel.model_name == model_name,
        )
    )
    allowed = result.scalar_one_or_none()

    if allowed and allowed.provider:
        provider = allowed.provider
        if provider.provider_type == "openai_compatible":
            return OpenAICompatibleClient(
                base_url=provider.base_url,
                api_key=provider.api_key,
            )

    # Default: Ollama
    return OllamaClient()


def get_llm_client_sync(
    model_name: str,
    tenant_id: UUID,
    db: AsyncSession,
) -> OllamaClient | OpenAICompatibleClient:
    """Synchronous wrapper for get_llm_client, for use in LangGraph nodes."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(get_llm_client(model_name, tenant_id, db))
    finally:
        loop.close()
