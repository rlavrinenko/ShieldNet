from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.core.events.types import Event

logger = logging.getLogger(__name__)

EventHandler = Callable[[Event], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class EventBusSnapshot:
    started: bool
    subscribers: int
    event_names: int
    published: int
    delivered: int
    failed: int
    active_dispatches: int
    average_dispatch_ms: float


class EventDispatchError(RuntimeError):
    def __init__(self, event: Event, failures: list[BaseException]) -> None:
        super().__init__(
            f"Event '{event.name}' failed in {len(failures)} subscriber(s)"
        )
        self.event = event
        self.failures = tuple(failures)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._started = False
        self._published = 0
        self._delivered = 0
        self._failed = 0
        self._active_dispatches = 0
        self._dispatch_time_ms = 0.0

    async def start(self) -> None:
        async with self._lock:
            self._started = True

    async def stop(self) -> None:
        async with self._lock:
            self._started = False

    async def subscribe(self, event_name: str, handler: EventHandler) -> None:
        normalized = event_name.strip()
        if not normalized:
            raise ValueError("Event name must not be empty")
        if not callable(handler):
            raise TypeError("Event handler must be callable")

        async with self._lock:
            handlers = self._subscribers[normalized]
            if handler not in handlers:
                handlers.append(handler)

    async def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        normalized = event_name.strip()
        async with self._lock:
            handlers = self._subscribers.get(normalized)
            if not handlers:
                return
            try:
                handlers.remove(handler)
            except ValueError:
                return
            if not handlers:
                self._subscribers.pop(normalized, None)

    async def publish(self, event: Event, *, raise_on_error: bool = False) -> None:
        if not self._started:
            raise RuntimeError("Event bus is not started")

        async with self._lock:
            handlers = tuple(self._subscribers.get(event.name, ())) + tuple(
                self._subscribers.get("*", ())
            )
            self._published += 1
            self._active_dispatches += 1

        started_at = perf_counter()
        failures: list[BaseException] = []
        try:
            if handlers:
                results = await asyncio.gather(
                    *(self._invoke(handler, event) for handler in handlers),
                    return_exceptions=True,
                )
                for result in results:
                    if isinstance(result, BaseException):
                        failures.append(result)

            async with self._lock:
                self._delivered += max(0, len(handlers) - len(failures))
                self._failed += len(failures)
        finally:
            elapsed_ms = (perf_counter() - started_at) * 1000
            async with self._lock:
                self._active_dispatches -= 1
                self._dispatch_time_ms += elapsed_ms

        if failures:
            logger.error(
                "event_dispatch_failed",
                extra={
                    "event_name": event.name,
                    "correlation_id": str(event.correlation_id),
                    "failures": len(failures),
                },
            )
            if raise_on_error:
                raise EventDispatchError(event, failures)

    async def snapshot(self) -> EventBusSnapshot:
        async with self._lock:
            average = (
                self._dispatch_time_ms / self._published
                if self._published
                else 0.0
            )
            return EventBusSnapshot(
                started=self._started,
                subscribers=sum(len(items) for items in self._subscribers.values()),
                event_names=len(self._subscribers),
                published=self._published,
                delivered=self._delivered,
                failed=self._failed,
                active_dispatches=self._active_dispatches,
                average_dispatch_ms=round(average, 3),
            )

    @staticmethod
    async def _invoke(handler: EventHandler, event: Event) -> None:
        result: Any = handler(event)
        if inspect.isawaitable(result):
            await result


event_bus = EventBus()
