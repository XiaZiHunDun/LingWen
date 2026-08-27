"""Dump FastAPI OpenAPI schema to a JSON file for zod reverse validation.

Usage:
    uv run python tooling/contracts/dump_openapi.py --base-url http://localhost:8765 --out /tmp/openapi.json

Or against a saved dump:
    uv run python tooling/contracts/dump_openapi.py --from-file /tmp/openapi.json --out /tmp/openapi.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8765")
    parser.add_argument("--out", default="/tmp/lingwen_openapi.json")
    parser.add_argument("--from-file", help="use a pre-saved openapi.json instead of fetching")
    args = parser.parse_args()

    if args.from_file:
        data = json.loads(Path(args.from_file).read_text(encoding="utf-8"))
    else:
        url = f"{args.base_url.rstrip('/')}/openapi.json"
        try:
            with urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"FAIL: cannot fetch OpenAPI from {url}: {exc}", file=sys.stderr)
            return 1

    Path(args.out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"WROTE {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
