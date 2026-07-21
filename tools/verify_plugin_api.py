#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', required=True)
    args = parser.parse_args()
    backend = Path(args.backend).resolve()
    sys.path.insert(0, str(backend))

    from app.api.router import api_router

    routes = []
    for route in api_router.routes:
        path = getattr(route, 'path', None)
        methods = sorted(getattr(route, 'methods', set()) or set())
        if path:
            for method in methods:
                if method not in {'HEAD', 'OPTIONS'}:
                    routes.append((method, path))

    duplicates = [item for item, count in Counter(routes).items() if count > 1]
    if duplicates:
        print('ERROR: duplicate routes detected:')
        for method, path in duplicates:
            print(f'  {method} {path}')
        return 2

    required = {
        ('GET', '/platform/plugins'),
        ('POST', '/platform/plugins/scan'),
        ('GET', '/platform/plugins/runtime'),
        ('GET', '/platform/plugin-events'),
        ('GET', '/platform/plugin-events/summary'),
    }
    found = set(routes)
    missing = sorted(required - found)
    if missing:
        print('ERROR: required plugin routes are missing:')
        for method, path in missing:
            print(f'  {method} {path}')
        return 3

    print(f'OK: {len(routes)} unique API method/path pairs registered.')
    for method, path in sorted(required):
        print(f'  {method} {path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
