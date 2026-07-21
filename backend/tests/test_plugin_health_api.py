from app.main import app


def test_plugin_health_route_is_registered() -> None:
    schema = app.openapi()
    operations = schema["paths"]["/api/v1/platform/plugins/health"]
    assert "get" in operations


def test_plugin_health_schema_is_exposed() -> None:
    schema = app.openapi()
    response = (
        schema["paths"]["/api/v1/platform/plugins/health"]["get"]
        ["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert response["$ref"].endswith("/PluginHealthResponse")
