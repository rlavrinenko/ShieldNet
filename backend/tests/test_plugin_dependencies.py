import pytest

from app.plugins.dependencies import PluginDependencyError, PluginDependencyResolver
from app.plugins.manifest import PluginManifest


def manifest(plugin_id: str, version: str = "1.0.0", dependencies=None) -> PluginManifest:
    return PluginManifest.from_dict(
        {
            "id": plugin_id,
            "name": plugin_id,
            "version": version,
            "dependencies": dependencies or {},
        }
    )


def test_dependencies_are_loaded_first() -> None:
    plan = PluginDependencyResolver().resolve(
        [manifest("reports", dependencies={"core-tools": ">=1.0.0"}), manifest("core-tools")]
    )
    assert [item.plugin_key for item in plan.ordered] == ["core-tools", "reports"]


def test_missing_dependency_is_rejected() -> None:
    with pytest.raises(PluginDependencyError, match="missing plugin"):
        PluginDependencyResolver().resolve([manifest("reports", dependencies={"core-tools": "1.0.0"})])


def test_dependency_cycle_is_rejected() -> None:
    with pytest.raises(PluginDependencyError, match="cycle"):
        PluginDependencyResolver().resolve(
            [
                manifest("plugin-a", dependencies={"plugin-b": "1.0.0"}),
                manifest("plugin-b", dependencies={"plugin-a": "1.0.0"}),
            ]
        )
