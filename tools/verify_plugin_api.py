#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ShieldNet Plugin API."
    )
    parser.add_argument(
        "--backend",
        required=True,
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
        ("GET", "/api/v1/platform/plugins"),
        ("POST", "/api/v1/platform/plugins/scan"),
        ("GET", "/api/v1/platform/plugins/runtime"),
        ("GET", "/api/v1/platform/plugin-events"),
        ("GET", "/api/v1/platform/plugin-events/summary"),
    }

    found: set[tuple[str, str]] = set()

    for path, path_data in paths.items():
        for method in path_data:
            normalized = method.upper()

            if normalized in {
                "GET", "POST", "PUT", "PATCH",
                "DELETE", "OPTIONS", "HEAD", "TRACE",
            }:
                found.add((normalized, path))

    missing = sorted(required - found)

    if missing:
        print("ERROR: required plugin API operations are missing:")
        for method, path in missing:
            print(f"  {method:7} {path}")
        return 4

    plugin_operations = sorted(
        (method, path)
        for method, path in found
        if "/platform/plugin" in path
    )

    print(
        f"OK: {len(plugin_operations)} Plugin API operations registered."
    )

    for method, path in plugin_operations:
        print(f"  {method:7} {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
