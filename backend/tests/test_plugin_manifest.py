import pytest

from app.plugins.manifest import PluginManifest, PluginManifestError


def test_valid_manifest_is_normalized() -> None:
    manifest = PluginManifest.from_dict(
        {
            "id": "Demo-Plugin",
            "name": " Demo Plugin ",
            "version": "1.2.3",
            "min_core": "7.0.0",
            "components": {"backend": True},
            "entrypoints": {"backend": "plugin_backend:Plugin"},
            "capabilities": ["translation", "translation"],
        }
    )
    assert manifest.plugin_key == "demo-plugin"
    assert manifest.capabilities == ("translation",)
    assert manifest.supports_core("7.0.0") is True
    assert manifest.supports_core("6.9.9") is False


def test_backend_entrypoint_is_required() -> None:
    with pytest.raises(PluginManifestError, match="entrypoints.backend"):
        PluginManifest.from_dict(
            {
                "id": "demo-plugin",
                "name": "Demo",
                "version": "1.0.0",
                "components": {"backend": True},
            }
        )


def test_invalid_version_is_rejected() -> None:
    with pytest.raises(PluginManifestError, match="semantic versioning"):
        PluginManifest.from_dict({"id": "demo-plugin", "name": "Demo", "version": "latest"})
