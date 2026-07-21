from app.main import app


REQUIRED_PLUGIN_ROUTES = {
    ("get", "/api/v1/platform/plugin-events"),
    ("get", "/api/v1/platform/plugin-events/summary"),
    ("get", "/api/v1/platform/plugins"),
    ("get", "/api/v1/platform/plugins/runtime"),
    ("post", "/api/v1/platform/plugins/scan"),
    ("patch", "/api/v1/platform/plugins/{plugin_key}"),
}


def _openapi_routes() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for path, operations in app.openapi().get("paths", {}).items():
        for method in operations:
            method = method.lower()
            if method in {
                "get", "post", "put", "patch", "delete",
                "head", "options", "trace",
            }:
                routes.add((method, path))
    return routes


def test_plugin_platform_routes_are_registered() -> None:
    missing = REQUIRED_PLUGIN_ROUTES - _openapi_routes()
    assert not missing, f"Missing routes: {sorted(missing)}"


def test_openapi_operation_ids_are_unique() -> None:
    operation_ids: list[str] = []
    for operations in app.openapi().get("paths", {}).values():
        for operation in operations.values():
            if isinstance(operation, dict) and operation.get("operationId"):
                operation_ids.append(operation["operationId"])

    duplicates = {
        value for value in operation_ids if operation_ids.count(value) > 1
    }
    assert not duplicates, f"Duplicate operation IDs: {sorted(duplicates)}"
