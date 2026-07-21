from app.main import app


REQUIRED = {
    ("post", "/api/v1/platform/plugin-marketplace/{plugin_key}/install"),
    ("post", "/api/v1/platform/plugin-marketplace/{plugin_key}/update"),
    ("post", "/api/v1/platform/plugin-marketplace/{plugin_key}/rollback"),
    ("post", "/api/v1/platform/plugin-marketplace/{plugin_key}/uninstall"),
    ("get", "/api/v1/platform/plugin-jobs"),
    ("get", "/api/v1/platform/plugin-jobs/{job_id}"),
}


def test_plugin_job_routes_registered() -> None:
    schema = app.openapi()
    found = {
        (method.lower(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    missing = REQUIRED - found
    assert not missing, f"Missing plugin job routes: {sorted(missing)}"
