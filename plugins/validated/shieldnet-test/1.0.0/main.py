from app.plugin_sdk import (
    CapabilityDenied,
    PluginBackendError,
    PluginContext,
)


async def setup(context: PluginContext):
    print("Plugin context:", context.public_info())

    backend_context = await context.backend.get_runtime_context()

    print(
        "Backend authenticated plugin:",
        backend_context["plugin_key"],
    )

    print(
        "Backend authenticated guild:",
        backend_context["guild_id"],
    )

    try:
        runtime_result = await context.backend.runtime_read()
    except CapabilityDenied as exc:
        print("runtime.read denied locally:", exc)
    else:
        print("runtime.read result:", runtime_result)

    try:
        await context.backend.test_send_message()
    except CapabilityDenied as exc:
        print(
            "discord.send.message denied locally:",
            exc,
        )
    except PluginBackendError as exc:
        print(
            "discord.send.message denied by Backend:",
            exc,
        )

    return {
        "status": "ready",
        "backend_authenticated": True,
    }


async def on_start(context: PluginContext):
    print(
        "Plugin started with capabilities:",
        sorted(context.permissions),
    )


async def on_stop(context: PluginContext):
    print("Plugin stopped")
