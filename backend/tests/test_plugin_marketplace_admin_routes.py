from app.main import app


REQUIRED = {
    ("get", "/api/v1/platform/plugin-marketplace"),
    ("get", "/api/v1/platform/plugin-marketplace/admin"),
    ("post", "/api/v1/platform/plugin-marketplace"),
    ("get", "/api/v1/platform/plugin-marketplace/{plugin_key}"),
    ("patch", "/api/v1/platform/plugin-marketplace/{plugin_key}"),
    ("delete", "/api/v1/platform/plugin-marketplace/{plugin_key}"),
    ("post", "/api/v1/platform/plugin-marketplace/{plugin_key}/versions"),
    ("patch", "/api/v1/platform/plugin-marketplace/{plugin_key}/publish"),
    ("patch", "/api/v1/platform/plugin-marketplace/{plugin_key}/verify"),
    (
        "delete",
        "/api/v1/platform/plugin-marketplace/{plugin_key}/versions/{version_id}",
    ),
}


def test_marketplace_administration_routes() -> None:
    schema = app.openapi()
    found = {
        (method.lower(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.lower() in {
            "get", "post", "put", "patch", "delete", "head", "options", "trace"
        }
    }
    missing = REQUIRED - found
    assert not missing, f"Missing Marketplace routes: {sorted(missing)}"


def test_static_admin_route_is_not_dynamic_plugin_key() -> None:
    schema = app.openapi()
    assert "/api/v1/platform/plugin-marketplace/admin" in schema["paths"]
