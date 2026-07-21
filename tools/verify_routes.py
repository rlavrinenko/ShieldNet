#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ShieldNet FastAPI route registration.")
    parser.add_argument("--backend", default="/opt/shieldnet/backend", help="Backend directory")
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
        print(f"ERROR: cannot import app.api.router: {exc!r}", file=sys.stderr)
        return 3

    signatures: list[tuple[str, str]] = []
    for route in api_router.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None) or {""}
        if not path:
            continue
        for method in methods:
            signatures.append((str(method), str(path)))

    counts = Counter(signatures)
    duplicates = sorted(sig for sig, count in counts.items() if count > 1)

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

    print(f"OK: {len(signatures)} method/path registrations; no duplicates.")
    for path in sorted(required):
        print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
