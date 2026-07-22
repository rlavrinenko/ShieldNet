#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


def iter_routes(router: Any, visited: set[int] | None = None) -> Iterator[Any]:
    """Recursively flatten FastAPI/Starlette routes, including _IncludeRouter."""

    if visited is None:
        visited = set()

    router_id = id(router)
    if router_id in visited:
        return

    visited.add(router_id)

    for route in getattr(router, "routes", []) or []:
        path = getattr(route, "path", None)

        if path is not None:
            yield route
            continue

        nested_router = getattr(route, "router", None)
        if nested_router is not None:
            yield from iter_routes(nested_router, visited)
            continue

        nested_routes = getattr(route, "routes", None)
        if nested_routes is not None:
            yield from iter_routes(route, visited)


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
        from app.api.router import api_router
    except Exception as exc:
        print(
            f"ERROR: cannot import app.api.router: {exc!r}",
            file=sys.stderr,
        )
        return 3

    signatures: list[tuple[str, str]] = []

    for route in iter_routes(api_router):
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or {""}

        if not path:
            continue

        for method in methods:
            method_name = str(method).upper()

            if method_name in {"HEAD", "OPTIONS"}:
                continue

            signatures.append((method_name, str(path)))

    counts = Counter(signatures)
    duplicates = sorted(
        signature
        for signature, count in counts.items()
        if count > 1
    )

    if duplicates:
        print("ERROR: duplicate API routes detected:")

        for method, path in duplicates:
            print(f"  {method:7} {path} x{counts[(method, path)]}")

        return 4

    required = {
        "/platform/plugins",
        "/platform/plugin-events",
        "/platform/plugin-events/summary",
        "/platform/plugins/runtime",
    }

    registered_paths = {path for _, path in signatures}
    missing = sorted(required - registered_paths)

    if missing:
        print("ERROR: required plugin routes are missing:")

        for path in missing:
            print(f"  {path}")

        return 5

    print(
        f"OK: {len(signatures)} method/path registrations; "
        "no duplicates."
    )

    for path in sorted(required):
        print(f"OK: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
