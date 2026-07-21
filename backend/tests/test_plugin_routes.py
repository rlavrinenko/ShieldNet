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
    schema = app.openapi()
    routes: set[tuple[str, str]] = set()

    for path, operations in schema.get("paths", {}).items():
        for method in operations:
            method = method.lower()
            if method in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "head",
                "options",
                "trace",
            }:
                routes.add((method, path))

    return routes


def test_plugin_platform_routes_are_registered() -> None:
    routes = _openapi_routes()
    missing = REQUIRED_PLUGIN_ROUTES - routes
    assert not missing, f"Missing routes: {sorted(missing)}"


def test_openapi_operation_ids_are_unique() -> None:
    schema = app.openapi()
    operation_ids: list[str] = []

    for operations in schema.get("paths", {}).values():
        for operation in operations.values():
            if isinstance(operation, dict):
                operation_id = operation.get("operationId")
                if operation_id:
                    operation_ids.append(operation_id)

    duplicates = {
        operation_id
        for operation_id in operation_ids
        if operation_ids.count(operation_id) > 1
    }

    assert not duplicates, f"Duplicate operation IDs: {sorted(duplicates)}"
