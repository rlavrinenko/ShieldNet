from app.plugin_sdk import (
    Capability,
    CapabilityDenied,
    PluginContext,
)


async def setup(context: PluginContext):
    print("Plugin context:", context.public_info())

    try:
        context.require(
            Capability.DISCORD_SEND_MESSAGE
        )
    except CapabilityDenied as exc:
        print("Expected permission denial:", exc)

    return {
        "status": "ready",
        "guild_id": context.guild_id,
        "plugin_key": context.plugin_key,
        "permissions": sorted(context.permissions),
    }


async def on_start(context: PluginContext):
    print(
        "Plugin started with capabilities:",
        sorted(context.permissions),
    )


async def on_stop(context: PluginContext):
    print("Plugin stopped")
