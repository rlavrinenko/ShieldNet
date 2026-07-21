import time
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_gateway import GuildAIProvider
from app.services.ai_secrets import AISecretService


DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "xai": "https://api.x.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "google_translate": "https://translation.googleapis.com/language/translate/v2",
    "deepl": "https://api-free.deepl.com/v2",
    "anthropic": "https://api.anthropic.com/v1",
}


class AIGatewayService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_provider(self, guild_id: int, provider_id: UUID) -> GuildAIProvider:
        result = await self.session.execute(select(GuildAIProvider).where(GuildAIProvider.id == provider_id, GuildAIProvider.guild_id == guild_id))
        provider = result.scalar_one_or_none()
        if provider is None:
            raise LookupError("AI provider not found")
        return provider

    async def test_provider(self, provider: GuildAIProvider) -> tuple[str, int, str]:
        started = time.perf_counter()
        api_key = AISecretService.decrypt(provider.encrypted_api_key)
        base = (provider.api_base_url or DEFAULT_BASE_URLS.get(provider.provider_type) or "").rstrip("/")
        if not base:
            raise ValueError("API base URL is required for this provider")

        headers = {"Accept": "application/json"}
        url = base
        if provider.provider_type in {"openai", "xai", "groq", "openai_compatible"}:
            headers["Authorization"] = f"Bearer {api_key}"
            url = f"{base}/models"
        elif provider.provider_type == "anthropic":
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
            url = f"{base}/models"
        elif provider.provider_type == "gemini":
            url = f"{base}/models?key={api_key}"
        elif provider.provider_type == "google_translate":
            url = f"{base}/languages?key={api_key}"
        elif provider.provider_type == "deepl":
            headers["Authorization"] = f"DeepL-Auth-Key {api_key}"
            url = f"{base}/languages"
        elif provider.provider_type == "libretranslate":
            url = f"{base}/languages"

        async with httpx.AsyncClient(timeout=provider.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
        latency = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            detail = response.text[:300] or f"HTTP {response.status_code}"
            return "error", latency, detail
        return "connected", latency, "Provider connection succeeded"
