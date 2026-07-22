#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ShieldNet FastAPI route registration."
    )
    parser.add_argument(
        "--backend",
        default="/opt/shieldnet/backend",
        help="Backend directory",
    )
    args = parser.parse_args()

    backend = Path(args.backend).resolve()

    if not (backend / "app").is_dir():
        print(f"ERROR: app package not found in {backend}", file=sys.stderr)
        return 2

    os.chdir(backend)
    sys.path.insert(0, str(backend))

    try:
        from app.main import app
        schema = app.openapi()
    except Exception as exc:
        print(f"ERROR: cannot generate OpenAPI schema: {exc!r}", file=sys.stderr)
        return 3

    paths = schema.get("paths", {})

    required = {
        "/api/v1/platform/plugins",
        "/api/v1/platform/plugins/runtime",
        "/api/v1/platform/plugin-events",
        "/api/v1/platform/plugin-events/summary",
    }

    missing = sorted(required - set(paths))

    if missing:
        print("ERROR: required plugin routes are missing:")
        for path in missing:
            print(f"  {path}")
        return 4

    operations = 0
    operation_ids: list[str] = []

    for path_data in paths.values():
        for method, operation in path_data.items():
            if method.lower() not in {
                "get", "post", "put", "patch", "delete",
                "options", "head", "trace",
            }:
                continue

            operations += 1

            operation_id = operation.get("operationId")
            if operation_id:
                operation_ids.append(operation_id)

    duplicate_ids = sorted({
        operation_id
        for operation_id in operation_ids
        if operation_ids.count(operation_id) > 1
    })

    if duplicate_ids:
        print("ERROR: duplicate OpenAPI operation IDs detected:")
        for operation_id in duplicate_ids:
            print(f"  {operation_id}")
        return 5

    print(
        f"OK: OpenAPI generated successfully: "
        f"{len(paths)} paths, {operations} operations."
    )

    for path in sorted(required):
        print(f"OK: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
