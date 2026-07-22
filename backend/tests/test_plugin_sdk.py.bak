import json
import tempfile
import unittest
from pathlib import Path

from app.plugins import PluginLoadError, PluginLoader, PluginManifestError, load_plugin_manifest


class PluginManifestTests(unittest.TestCase):
    def test_manifest_normalizes_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "Example_Plugin",
                        "name": " Example ",
                        "version": "1.0.0",
                        "capabilities": ["audit", "audit", ""],
                    }
                ),
                encoding="utf-8",
            )
            manifest, _, checksum = load_plugin_manifest(path)
            self.assertEqual(manifest.id, "example_plugin")
            self.assertEqual(manifest.name, "Example")
            self.assertEqual(manifest.capabilities, ["audit"])
            self.assertEqual(len(checksum), 64)

    def test_manifest_rejects_invalid_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plugin.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "example-plugin",
                        "name": "Example",
                        "version": "1.0.0",
                        "backend_entrypoint": "../escape:Plugin",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(PluginManifestError):
                load_plugin_manifest(path)


class PluginLoaderTests(unittest.IsolatedAsyncioTestCase):
    async def test_load_start_health_stop_unload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "example-plugin"
            plugin.mkdir()
            (plugin / "plugin.json").write_text(
                json.dumps(
                    {
                        "id": "example-plugin",
                        "name": "Example",
                        "version": "1.0.0",
                        "components": {"backend": True},
                        "backend_entrypoint": "backend.plugin:Plugin",
                    }
                ),
                encoding="utf-8",
            )
            (plugin / "backend").mkdir()
            (plugin / "backend" / "plugin.py").write_text(
                "from app.plugins import ShieldNetPlugin\n"
                "class Plugin(ShieldNetPlugin):\n"
                "    async def startup(self):\n"
                "        self.running = True\n"
                "    async def shutdown(self):\n"
                "        self.running = False\n"
                "    async def healthcheck(self):\n"
                "        return {'status': 'healthy', 'running': getattr(self, 'running', False)}\n",
                encoding="utf-8",
            )

            loader = PluginLoader(root)
            loaded = loader.load(plugin)
            self.assertFalse(loaded.started)
            await loader.start("example-plugin")
            health = await loader.healthcheck("example-plugin")
            self.assertTrue(health["running"])
            await loader.stop("example-plugin")
            loader.unload("example-plugin")
            self.assertNotIn("example-plugin", loader.loaded)

    async def test_backend_component_requires_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin = root / "broken-plugin"
            plugin.mkdir()
            (plugin / "plugin.json").write_text(
                json.dumps(
                    {
                        "id": "broken-plugin",
                        "name": "Broken",
                        "version": "1.0.0",
                        "components": {"backend": True},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(PluginLoadError):
                PluginLoader(root).load(plugin)


if __name__ == "__main__":
    unittest.main()
