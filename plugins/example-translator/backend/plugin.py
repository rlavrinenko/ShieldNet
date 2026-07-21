from app.plugins import ShieldNetPlugin


class Plugin(ShieldNetPlugin):
    async def healthcheck(self) -> dict[str, object]:
        return {"status": "healthy", "plugin": self.context.plugin_key}
