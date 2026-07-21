from __future__ import annotations

from dataclasses import dataclass

from app.plugins.manifest import PluginManifest, Version


class PluginDependencyError(RuntimeError):
    pass


@dataclass(frozen=True)
class DependencyPlan:
    ordered: tuple[PluginManifest, ...]


class PluginDependencyResolver:
    """Validates plugin dependencies and returns a deterministic load order."""

    def resolve(self, manifests: list[PluginManifest]) -> DependencyPlan:
        by_key = {manifest.plugin_key: manifest for manifest in manifests}
        if len(by_key) != len(manifests):
            raise PluginDependencyError("Duplicate plugin ids were supplied")

        for manifest in manifests:
            for dependency_key, minimum_version in manifest.dependencies.items():
                dependency = by_key.get(dependency_key)
                if dependency is None:
                    raise PluginDependencyError(
                        f"Plugin {manifest.plugin_key} requires missing plugin {dependency_key}"
                    )
                if minimum_version and Version.parse(dependency.version) < Version.parse(
                    minimum_version,
                    field_name=f"dependencies.{dependency_key}",
                ):
                    raise PluginDependencyError(
                        f"Plugin {manifest.plugin_key} requires {dependency_key}>={minimum_version}, "
                        f"installed {dependency.version}"
                    )

        temporary: set[str] = set()
        permanent: set[str] = set()
        result: list[PluginManifest] = []

        def visit(plugin_key: str, trail: tuple[str, ...]) -> None:
            if plugin_key in permanent:
                return
            if plugin_key in temporary:
                cycle = " -> ".join((*trail, plugin_key))
                raise PluginDependencyError(f"Plugin dependency cycle detected: {cycle}")
            temporary.add(plugin_key)
            manifest = by_key[plugin_key]
            for dependency_key in sorted(manifest.dependencies):
                visit(dependency_key, (*trail, plugin_key))
            temporary.remove(plugin_key)
            permanent.add(plugin_key)
            result.append(manifest)

        for key in sorted(by_key):
            visit(key, ())

        return DependencyPlan(ordered=tuple(result))
