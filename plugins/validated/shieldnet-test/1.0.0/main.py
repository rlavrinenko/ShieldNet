from __future__ import annotations

import asyncio
from typing import Any

from app.plugin_sdk import (
    CapabilityDenied,
    PluginBackendAuthenticationError,
    PluginBackendError,
    PluginContext,
)


_background_tasks: set[asyncio.Task[Any]] = set()


def create_background_task(
    coroutine,
    *,
    name: str,
) -> asyncio.Task[Any]:
    task = asyncio.create_task(
        coroutine,
        name=name,
    )

    _background_tasks.add(task)

    def task_done(
        completed_task: asyncio.Task[Any],
    ) -> None:
        _background_tasks.discard(completed_task)

        if completed_task.cancelled():
            return

        try:
            exception = completed_task.exception()
        except asyncio.CancelledError:
            return

        if exception is not None:
            print(
                f"Background task '{name}' failed:",
                repr(exception),
            )

    task.add_done_callback(task_done)

    return task


async def token_rotation_test(
    context: PluginContext,
) -> None:
    backend = context.backend
    initial_expiry = backend.token_expires_at

    print(
        "Initial Runtime Token expires:",
        initial_expiry.isoformat(),
    )

    while True:
        try:
            await asyncio.sleep(20)

            result = await backend.get_runtime_context()
            current_expiry = backend.token_expires_at

            print(
                "Runtime Token check:",
                current_expiry.isoformat(),
                "plugin:",
                result["plugin_key"],
            )

            if current_expiry > initial_expiry:
                print(
                    "Runtime Token automatically rotated:",
                    initial_expiry.isoformat(),
                    "->",
                    current_expiry.isoformat(),
                )
                return

        except asyncio.CancelledError:
            print("Runtime Token test task cancelled")
            raise

        except PluginBackendAuthenticationError as exc:
            print(
                "Runtime Token became inactive:",
                exc,
            )
            return

        except PluginBackendError as exc:
            print(
                "Runtime Token temporary request error:",
                exc,
            )

            await asyncio.sleep(10)


async def setup(context: PluginContext):
    backend_context = (
        await context.backend.get_runtime_context()
    )

    print(
        "Backend authenticated plugin:",
        backend_context["plugin_key"],
    )

    print(
        "Backend authenticated guild:",
        backend_context["guild_id"],
    )

    try:
        runtime_result = (
            await context.backend.runtime_read()
        )
    except CapabilityDenied as exc:
        print("runtime.read denied locally:", exc)
    else:
        print("runtime.read result:", runtime_result)

    return {
        "status": "ready",
        "backend_authenticated": True,
    }


async def on_start(context: PluginContext):
    print(
        "Plugin started with capabilities:",
        sorted(context.permissions),
    )

    create_background_task(
        token_rotation_test(context),
        name="shieldnet-token-rotation-test",
    )


async def on_stop(context: PluginContext):
    print(
        "Stopping plugin background tasks:",
        len(_background_tasks),
    )

    tasks = list(_background_tasks)

    for task in tasks:
        task.cancel()

    if tasks:
        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    _background_tasks.clear()

    print("Plugin stopped")
