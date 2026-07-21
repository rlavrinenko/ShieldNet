from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from app.plugins.context import PluginContext
from app.plugins.contracts import ShieldNetPlugin
from app.plugins.manifest import PluginManifest, PluginManifestError, load_plugin_manifest


class PluginLoadError(RuntimeError):
    pass


@dataclass(slots=True)
class LoadedPlugin:
    manifest: PluginManifest
    root: Path
    instance: ShieldNetPlugin | None
    started: bool = False


class PluginLoader:
    def __init__(self, plugin_root: Path) -> None:
        self.plugin_root = plugin_root.resolve()
        self.loaded: dict[str, LoadedPlugin] = {}

    def discover(self) -> list[tuple[Path, PluginManifest]]:
        self.plugin_root.mkdir(parents=True, exist_ok=True)
        discovered: list[tuple[Path, PluginManifest]] = []
        for path in sorted(self.plugin_root.glob("*/plugin.json")):
            manifest, _, _ = load_plugin_manifest(path)
            discovered.append((path.parent.resolve(), manifest))
        return discovered

    def load(self, plugin_dir: Path) -> LoadedPlugin:
        plugin_dir = plugin_dir.resolve()
        self._ensure_inside_root(plugin_dir)
        manifest, _, _ = load_plugin_manifest(plugin_dir / "plugin.json")

        existing = self.loaded.get(manifest.id)
        if existing is not None:
            return existing

        instance: ShieldNetPlugin | None = None
        if manifest.components.backend:
            if not manifest.backend_entrypoint:
                raise PluginLoadError(
                    f"{manifest.id}: backend component requires backend_entrypoint"
                )
            module_name, class_name = manifest.backend_entrypoint.split(":", 1)
            module = self._load_module(manifest.id, plugin_dir, module_name)
            plugin_class = getattr(module, class_name, None)
            if plugin_class is None or not inspect.isclass(plugin_class):
                raise PluginLoadError(
                    f"{manifest.id}: entrypoint class {class_name!r} was not found"
                )
            if not issubclass(plugin_class, ShieldNetPlugin):
                raise PluginLoadError(
                    f"{manifest.id}: {class_name} must inherit ShieldNetPlugin"
                )
            context = PluginContext(
                plugin_key=manifest.id,
                plugin_root=plugin_dir,
                manifest=manifest.registry_payload(),
            )
            instance = plugin_class(context)

        loaded = LoadedPlugin(manifest=manifest, root=plugin_dir, instance=instance)
        self.loaded[manifest.id] = loaded
        return loaded

    async def start(self, plugin_key: str) -> LoadedPlugin:
        loaded = self._required(plugin_key)
        if loaded.started:
            return loaded
        if loaded.instance is not None:
            await loaded.instance.startup()
        loaded.started = True
        return loaded

    async def stop(self, plugin_key: str) -> LoadedPlugin:
        loaded = self._required(plugin_key)
        if not loaded.started:
            return loaded
        if loaded.instance is not None:
            await loaded.instance.shutdown()
        loaded.started = False
        return loaded

    async def healthcheck(self, plugin_key: str) -> dict[str, object]:
        loaded = self._required(plugin_key)
        if loaded.instance is None:
            return {"status": "healthy", "component": "manifest-only"}
        result = await loaded.instance.healthcheck()
        if not isinstance(result, dict):
            raise PluginLoadError(f"{plugin_key}: healthcheck must return a dictionary")
        return result

    def unload(self, plugin_key: str) -> None:
        loaded = self._required(plugin_key)
        if loaded.started:
            raise PluginLoadError(f"{plugin_key}: stop plugin before unloading")
        self.loaded.pop(plugin_key, None)
        prefix = f"shieldnet_plugin_{plugin_key.replace('-', '_')}"
        for name in list(sys.modules):
            if name == prefix or name.startswith(prefix + "."):
                sys.modules.pop(name, None)

    def _load_module(self, plugin_key: str, plugin_dir: Path, module_name: str) -> ModuleType:
        relative = Path(*module_name.split("."))
        module_path = plugin_dir / relative.with_suffix(".py")
        package_init = plugin_dir / relative / "__init__.py"
        if module_path.is_file():
            source = module_path
            submodule_locations = None
        elif package_init.is_file():
            source = package_init
            submodule_locations = [str(package_init.parent)]
        else:
            raise PluginLoadError(
                f"{plugin_key}: module {module_name!r} does not exist inside plugin directory"
            )

        source = source.resolve()
        self._ensure_inside_plugin(plugin_dir, source)
        runtime_name = (
            f"shieldnet_plugin_{plugin_key.replace('-', '_')}."
            f"{module_name}"
        )
        spec = importlib.util.spec_from_file_location(
            runtime_name,
            source,
            submodule_search_locations=submodule_locations,
        )
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"{plugin_key}: unable to create module specification")
        module = importlib.util.module_from_spec(spec)
        sys.modules[runtime_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(runtime_name, None)
            raise PluginLoadError(f"{plugin_key}: import failed: {exc}") from exc
        return module

    def _required(self, plugin_key: str) -> LoadedPlugin:
        try:
            return self.loaded[plugin_key]
        except KeyError as exc:
            raise PluginLoadError(f"{plugin_key}: plugin is not loaded") from exc

    def _ensure_inside_root(self, path: Path) -> None:
        try:
            path.relative_to(self.plugin_root)
        except ValueError as exc:
            raise PluginLoadError(f"plugin path escapes plugin root: {path}") from exc

    @staticmethod
    def _ensure_inside_plugin(plugin_dir: Path, path: Path) -> None:
        try:
            path.relative_to(plugin_dir)
        except ValueError as exc:
            raise PluginLoadError(f"module path escapes plugin directory: {path}") from exc
