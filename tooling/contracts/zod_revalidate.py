"""zod reverse validation for lingwen-shared contracts.

Compares Pydantic-derived TypeScript types against zod schemas generated
from the FastAPI OpenAPI schema. Detects drift between Python source of
truth and the live API contract.

v16.1 status: runs as an independent CI job (Q5=B), not in the dev loop.

Usage:
    # 1. dump OpenAPI from running backend
    uv run python tooling/contracts/dump_openapi.py --out /tmp/openapi.json
    # 2. compare
    uv run python tooling/contracts/zod_revalidate.py --openapi /tmp/openapi.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_TS_DIR = REPO_ROOT / "packages" / "lingwen-shared" / "src" / "lingwen_shared" / "contracts" / "ts"


def _extract_required_fields_from_ts(ts_content: str, interface_name: str) -> set[str]:
    """Extract required field names from a TS interface.

    Heuristic: any property without `?` after the colon is required.
    """
    pattern = re.compile(
        rf"interface\s+{interface_name}\s*\{{(.*?)\}}",
        re.DOTALL,
    )
    m = pattern.search(ts_content)
    if not m:
        return set()
    body = m.group(1)
    required: set[str] = set()
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("/*"):
            continue
        # e.g. `id: number;` (required) or `name?: string;` (optional)
        m2 = re.match(r"(\w+)(\??)\s*:", line)
        if not m2:
            continue
        field, opt = m2.group(1), m2.group(2)
        if opt != "?":
            required.add(field)
    return required


def _extract_required_fields_from_openapi(schema: dict, model_name: str) -> set[str] | None:
    """Look up a schema by name in components.schemas and return required fields."""
    schemas = schema.get("components", {}).get("schemas", {})
    target = schemas.get(model_name)
    if not isinstance(target, dict):
        return None
    return set(target.get("required", []))


def _ts_interfaces_in_module(ts_path: Path) -> set[str]:
    content = ts_path.read_text(encoding="utf-8")
    return set(re.findall(r"interface\s+(\w+)", content))


def compare() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openapi", required=True, help="Path to OpenAPI JSON dump")
    args = parser.parse_args()

    openapi_path = Path(args.openapi)
    if not openapi_path.is_file():
        print(f"FAIL: {openapi_path} not found", file=sys.stderr)
        return 1
    schema = json.loads(openapi_path.read_text(encoding="utf-8"))

    drift: list[str] = []
    modules = (
        "world",
        "workspace",
        "quality",
        "creator",
        "health",
        "studio",
        "workflows",
        "cvg",
        "decisions",
    )
    for mod in modules:
        ts_file = SHARED_TS_DIR / f"{mod}.ts"
        if not ts_file.is_file():
            print(f"WARN: {ts_file} missing — skipping module {mod}")
            continue
        for iface in _ts_interfaces_in_module(ts_file):
            ts_required = _extract_required_fields_from_ts(ts_file.read_text(encoding="utf-8"), iface)
            oa_required = _extract_required_fields_from_openapi(schema, iface)
            if oa_required is None:
                continue  # not in OpenAPI — OK (DTO not yet exposed via API)
            if ts_required != oa_required:
                drift.append(
                    f"DRIFT {mod}.{iface}: TS required={sorted(ts_required)} "
                    f"!= OpenAPI required={sorted(oa_required)}"
                )

    if drift:
        print("zod reverse validation FAILED:")
        for d in drift:
            print(f"  - {d}")
        return 1
    print("zod reverse validation OK (no drift detected)")
    return 0


def main() -> int:
    return compare()


if __name__ == "__main__":
    sys.exit(main())
