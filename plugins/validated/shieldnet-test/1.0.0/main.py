import asyncio

from app.plugin_sdk import (
    CapabilityDenied,
    PluginBackendError,
    PluginContext,
)


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
        await asyncio.sleep(20)

        try:
            result = await backend.get_runtime_context()
        except PluginBackendError as exc:
            print(
                "Runtime Token request failed:",
                exc,
            )
            raise

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


async def setup(context: PluginContext):
    backend = context.backend

    backend_context = await backend.get_runtime_context()

    print(
        "Backend authenticated plugin:",
        backend_context["plugin_key"],
    )

    try:
        runtime_result = await backend.runtime_read()
    except CapabilityDenied as exc:
        print("runtime.read denied locally:", exc)
    else:
        print("runtime.read result:", runtime_result)

    return {
        "status": "ready",
    }


async def on_start(context: PluginContext):
    print(
        "Plugin started with capabilities:",
        sorted(context.permissions),
    )

    asyncio.create_task(
        token_rotation_test(context),
        name="shieldnet-token-rotation-test",
    )


async def on_stop(context: PluginContext):
    print("Plugin stopped")
