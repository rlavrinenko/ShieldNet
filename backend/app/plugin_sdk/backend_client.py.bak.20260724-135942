from __future__ import annotations

import json as jsonlib
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit

import httpx

from app.plugin_sdk.capabilities import (
    Capability,
    PluginContext,
)


class PluginBackendError(RuntimeError):
    """Base error raised by the ShieldNet Plugin Backend SDK."""


class PluginBackendAuthenticationError(PluginBackendError):
    pass


class PluginBackendPermissionError(PluginBackendError):
    pass


class PluginBackendRateLimitError(PluginBackendError):
    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message)


class PluginBackendUnavailableError(PluginBackendError):
    pass


class PluginBackendResponseError(PluginBackendError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
    ) -> None:
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PluginBackendResponse:
    status_code: int
    data: Any
    request_id: str | None


class PluginBackendClient:
    def __init__(
        self,
        *,
        context: PluginContext,
        timeout_seconds: float = 15.0,
        max_response_bytes: int = 2 * 1024 * 1024,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 120:
            raise ValueError(
                "timeout_seconds must be between 0 and 120"
            )

        if max_response_bytes < 1024:
            raise ValueError(
                "max_response_bytes must be at least 1024"
            )

        backend_url = context.backend_url.rstrip("/")

        parsed = urlsplit(backend_url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "ShieldNet Backend URL must use HTTP or HTTPS"
            )

        if not parsed.hostname:
            raise ValueError(
                "ShieldNet Backend URL has no hostname"
            )

        self._context = context
        self._backend_url = backend_url
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_response_bytes = max_response_bytes

    @property
    def plugin_key(self) -> str:
        return self._context.plugin_key

    @property
    def guild_id(self) -> int:
        return self._context.guild_id

    def _validate_path(self, path: str) -> str:
        if not isinstance(path, str) or not path:
            raise ValueError("Backend API path is required")

        parsed = urlsplit(path)

        if parsed.scheme or parsed.netloc:
            raise ValueError(
                "Absolute URLs are not allowed in Plugin SDK"
            )

        if not path.startswith("/"):
            raise ValueError(
                "Backend API path must start with '/'"
            )

        path_segments = parsed.path.split("/")

        if ".." in path_segments:
            raise ValueError(
                "Parent path traversal is not allowed"
            )

        if not parsed.path.startswith(
            "/internal/plugin-runtime/"
        ):
            raise ValueError(
                "Plugin SDK may access only "
                "/internal/plugin-runtime endpoints"
            )

        return path

    @staticmethod
    def _safe_error_detail(
        content: bytes,
    ) -> str:
        if not content:
            return "ShieldNet Backend rejected the request"

        try:
            payload = jsonlib.loads(
                content.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            jsonlib.JSONDecodeError,
        ):
            return "ShieldNet Backend rejected the request"

        if isinstance(payload, dict):
            detail = payload.get("detail")

            if isinstance(detail, str):
                return detail[:500]

            if isinstance(detail, list):
                return str(detail)[:500]

        return "ShieldNet Backend rejected the request"

    async def request(
        self,
        method: str,
        path: str,
        *,
        capability: Capability | str | None = None,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
    ) -> PluginBackendResponse:
        safe_path = self._validate_path(path)

        if capability is not None:
            self._context.require(capability)

        headers = {
            "Authorization": (
                f"Bearer {self._context.runtime_token}"
            ),
            "Accept": "application/json",
            "User-Agent": (
                f"ShieldNet-Plugin/{self.plugin_key}"
            ),
            "X-ShieldNet-Plugin-Key": self.plugin_key,
            "X-ShieldNet-Guild-ID": str(self.guild_id),
            "X-ShieldNet-Generation": str(
                self._context.generation
            ),
        }

        try:
            async with httpx.AsyncClient(
                base_url=self._backend_url,
                timeout=self._timeout,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                async with client.stream(
                    method=method.upper(),
                    url=safe_path,
                    headers=headers,
                    json=json,
                    params=params,
                ) as response:
                    body = bytearray()

                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)

                        if len(body) > self._max_response_bytes:
                            raise PluginBackendResponseError(
                                "ShieldNet Backend response "
                                "exceeded the SDK size limit",
                                status_code=response.status_code,
                            )

                    content = bytes(body)

        except httpx.TimeoutException as exc:
            raise PluginBackendUnavailableError(
                "ShieldNet Backend request timed out"
            ) from exc
        except httpx.NetworkError as exc:
            raise PluginBackendUnavailableError(
                "ShieldNet Backend is unavailable"
            ) from exc

        request_id = response.headers.get("X-Request-ID")

        if response.status_code == 401:
            raise PluginBackendAuthenticationError(
                self._safe_error_detail(content)
            )

        if response.status_code == 403:
            raise PluginBackendPermissionError(
                self._safe_error_detail(content)
            )

        if response.status_code == 429:
            retry_after: float | None = None
            raw_retry_after = response.headers.get("Retry-After")

            if raw_retry_after:
                try:
                    retry_after = float(raw_retry_after)
                except ValueError:
                    retry_after = None

            raise PluginBackendRateLimitError(
                self._safe_error_detail(content),
                retry_after=retry_after,
            )

        if response.status_code >= 500:
            raise PluginBackendUnavailableError(
                "ShieldNet Backend returned a server error"
            )

        if response.status_code >= 400:
            raise PluginBackendResponseError(
                self._safe_error_detail(content),
                status_code=response.status_code,
            )

        if not content:
            data: Any = None
        else:
            try:
                data = jsonlib.loads(
                    content.decode("utf-8")
                )
            except (
                UnicodeDecodeError,
                jsonlib.JSONDecodeError,
            ) as exc:
                raise PluginBackendResponseError(
                    "ShieldNet Backend returned invalid JSON",
                    status_code=response.status_code,
                ) from exc

        return PluginBackendResponse(
            status_code=response.status_code,
            data=data,
            request_id=request_id,
        )

    async def get_runtime_context(
        self,
    ) -> dict[str, Any]:
        response = await self.request(
            "GET",
            "/internal/plugin-runtime/context",
        )

        if not isinstance(response.data, dict):
            raise PluginBackendResponseError(
                "Invalid runtime context response",
                status_code=response.status_code,
            )

        return response.data

    async def runtime_read(
        self,
    ) -> dict[str, Any]:
        response = await self.request(
            "POST",
            "/internal/plugin-runtime/test/runtime-read",
            capability=Capability.RUNTIME_READ,
        )

        if not isinstance(response.data, dict):
            raise PluginBackendResponseError(
                "Invalid runtime.read response",
                status_code=response.status_code,
            )

        return response.data

    async def test_send_message(
        self,
    ) -> dict[str, Any]:
        response = await self.request(
            "POST",
            "/internal/plugin-runtime/test/send-message",
            capability=Capability.DISCORD_SEND_MESSAGE,
        )

        if not isinstance(response.data, dict):
            raise PluginBackendResponseError(
                "Invalid send-message response",
                status_code=response.status_code,
            )

        return response.data
