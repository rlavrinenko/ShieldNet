from __future__ import annotations

import logging
from dataclasses import dataclass

import discord
import httpx

from bot.backend import BackendAIError, BackendClient

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class TranslationResult:
    text: str
    provider_name: str
    provider_type: str
    model: str | None
    latency_ms: int


class TranslatorClient:
    """Thin Discord-side adapter for the per-guild ShieldNet AI Gateway."""

    def __init__(self, backend: BackendClient) -> None:
        self.backend = backend

    async def translate(
        self,
        *,
        guild_id: int,
        user_id: int,
        channel_id: int | None,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        payload = await self.backend.execute_ai(
            guild_id=guild_id,
            module_key="translator",
            capability="translation",
            input_text=text,
            source_language=source_language,
            target_language=target_language,
            metadata={
                "origin": "discord_slash_command",
                "discord_user_id": str(user_id),
                "discord_channel_id": str(channel_id) if channel_id else None,
            },
        )
        return TranslationResult(
            text=str(payload.get("text") or "").strip(),
            provider_name=str(payload.get("provider_name") or "Unknown"),
            provider_type=str(payload.get("provider_type") or "unknown"),
            model=payload.get("model"),
            latency_ms=int(payload.get("latency_ms") or 0),
        )

    @staticmethod
    def user_error_message(exc: Exception) -> str:
        if isinstance(exc, BackendAIError):
            if exc.status_code == 404:
                return (
                    "Translator AI is not configured for this server. "
                    "A server administrator must assign an enabled provider to "
                    "translator / translation in ShieldNet."
                )
            if exc.status_code == 422:
                return f"Translation request is invalid: {exc.detail}"
            if exc.status_code == 502:
                return "All configured translation providers failed. Please try again later."
            return f"ShieldNet AI error: {exc.detail}"
        if isinstance(exc, httpx.TimeoutException):
            return "The translation provider did not respond in time."
        if isinstance(exc, httpx.HTTPError):
            return "ShieldNet backend is temporarily unavailable."
        return "The translation could not be completed."


def translation_embed(result: TranslationResult, source: str, target: str) -> discord.Embed:
    description = result.text or "(empty response)"
    if len(description) > 4096:
        description = description[:4093] + "..."
    embed = discord.Embed(
        title=f"Translation: {source} → {target}",
        description=description,
    )
    provider = result.provider_name
    if result.model:
        provider += f" · {result.model}"
    embed.set_footer(text=f"{provider} · {result.latency_ms} ms")
    return embed
