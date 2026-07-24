PLUGIN_NAME = "ShieldNet Test Plugin"
PLUGIN_VERSION = "1.0.0"


async def setup(context):
    return {
        "status": "ready",
        "plugin": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
    }
