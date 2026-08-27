"""Turbo config verification for v16.0 Phase 124.

Validates that turbo.json schema and root package.json scripts are coherent.
Pure structural check — does NOT execute turbo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TURBO_JSON = REPO_ROOT / "turbo.json"
PACKAGE_JSON = REPO_ROOT / "package.json"


def _check_turbo_tasks_match_scripts() -> list[str]:
    """turbo.json pipeline keys must be referenced from package.json scripts."""
    turbo = json.loads(TURBO_JSON.read_text(encoding="utf-8"))
    pkg = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    turbo_tasks = set(turbo.get("tasks", {}).keys())
    scripts = pkg.get("scripts", {})
    mismatches: list[str] = []
    for script_name, script_body in scripts.items():
        if "turbo run" not in script_body:
            continue
        # extract the turbo task name (first word after 'turbo run')
        parts = script_body.split()
        if len(parts) < 3 or parts[0] != "turbo" or parts[1] != "run":
            continue
        task = parts[2]
        if task not in turbo_tasks:
            mismatches.append(
                f"package.json script {script_name!r} runs 'turbo run {task}' "
                f"but turbo.json has no pipeline.{task} entry"
            )
    return mismatches


def _check_required_pipeline_keys() -> list[str]:
    """turbo.json should at minimum have build/test/lint/typecheck tasks."""
    turbo = json.loads(TURBO_JSON.read_text(encoding="utf-8"))
    pipeline = turbo.get("tasks", {})
    required = {"build", "test", "lint", "typecheck"}
    missing = required - pipeline.keys()
    return [f"turbo.json missing required tasks.{m}" for m in missing]


def main() -> int:
    errors = []
    errors.extend(_check_required_pipeline_keys())
    errors.extend(_check_turbo_tasks_match_scripts())
    if errors:
        print("Turbo config check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: turbo.json schema + root scripts are coherent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
