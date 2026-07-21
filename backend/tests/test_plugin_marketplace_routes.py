from app.main import app


def test_marketplace_routes_are_registered() -> None:
    schema = app.openapi()
    assert "/api/v1/platform/plugin-marketplace" in schema["paths"]
    assert "/api/v1/platform/plugin-marketplace/{plugin_key}" in schema["paths"]
    assert "get" in schema["paths"]["/api/v1/platform/plugin-marketplace"]
    assert "get" in schema["paths"]["/api/v1/platform/plugin-marketplace/{plugin_key}"]
