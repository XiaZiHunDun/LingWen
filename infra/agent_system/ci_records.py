"""Phase 9.98 F90: CI run records (e2e-live first-green JSON in infra/.state/ci_records)."""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

E2E_LIVE_FIRST_GREEN_FILENAME = "e2e-live-first-green.json"
E2E_LIVE_WORKFLOW = "test.yml"
E2E_LIVE_JOB_NAME = "Playwright live-backend (5 specs)"
E2E_LIVE_SUMMARY_PHRASE = "Playwright live-backend — passed"
E2E_LIVE_TESTS_PASSED = 5
E2E_LIVE_VERIFY_SCRIPT = "novel-factory/scripts/verify-e2e-live-ci.sh"


def default_ci_records_dir() -> Path:
    """Default: novel-factory/infra/.state/ci_records (override via env)."""
    env = os.environ.get("LINGWEN_CI_RECORDS_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / ".state" / "ci_records"


def default_e2e_live_first_green_path() -> Path:
    return default_ci_records_dir() / E2E_LIVE_FIRST_GREEN_FILENAME


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_e2e_live_first_green_record(data: dict[str, Any]) -> list[str]:
    """Return validation error messages (empty list = valid)."""
    errors: list[str] = []
    required = (
        "record_id",
        "workflow",
        "trigger",
        "branch",
        "github_run_id",
        "github_run_url",
        "job_name",
        "tests_passed",
        "summary_phrase",
        "local_parity",
        "operator",
        "recorded_at",
    )
    for key in required:
        if key not in data:
            errors.append(f"missing field: {key}")

    local = data.get("local_parity")
    if not isinstance(local, dict):
        errors.append("local_parity must be an object")
    else:
        if local.get("script") != E2E_LIVE_VERIFY_SCRIPT:
            errors.append(f"local_parity.script must be {E2E_LIVE_VERIFY_SCRIPT!r}")
        if local.get("passed") is not True:
            errors.append("local_parity.passed must be true")
        if not local.get("verified_at"):
            errors.append("local_parity.verified_at required")

    tests = data.get("tests_passed")
    if tests != E2E_LIVE_TESTS_PASSED:
        errors.append(f"tests_passed must be {E2E_LIVE_TESTS_PASSED}")

    if data.get("workflow") != E2E_LIVE_WORKFLOW:
        errors.append(f"workflow must be {E2E_LIVE_WORKFLOW!r}")

    if data.get("summary_phrase") != E2E_LIVE_SUMMARY_PHRASE:
        errors.append(f"summary_phrase must be {E2E_LIVE_SUMMARY_PHRASE!r}")

    return errors


def build_e2e_live_first_green_record(
    *,
    github_run_id: str,
    github_run_url: str,
    operator: str,
    local_parity_passed: bool = True,
    local_verified_at: str | None = None,
    trigger: str = "workflow_dispatch",
    branch: str = "master",
    recorded_at: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build a validated e2e-live first-green record dict."""
    now = recorded_at or _utc_now_iso()
    record: dict[str, Any] = {
        "record_id": "e2e-live-first-green",
        "workflow": E2E_LIVE_WORKFLOW,
        "trigger": trigger,
        "branch": branch,
        "github_run_id": github_run_id,
        "github_run_url": github_run_url,
        "job_name": E2E_LIVE_JOB_NAME,
        "tests_passed": E2E_LIVE_TESTS_PASSED,
        "summary_phrase": E2E_LIVE_SUMMARY_PHRASE,
        "local_parity": {
            "script": E2E_LIVE_VERIFY_SCRIPT,
            "passed": local_parity_passed,
            "verified_at": local_verified_at or now,
        },
        "operator": operator,
        "recorded_at": now,
    }
    if notes:
        record["notes"] = notes
    errors = validate_e2e_live_first_green_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    return record


def load_e2e_live_first_green_record(
    path: Path | None = None,
) -> dict[str, Any] | None:
    target = path or default_e2e_live_first_green_path()
    if not target.is_file():
        return None
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"record must be a JSON object: {target}")
    return data


def write_e2e_live_first_green_record(
    record: dict[str, Any],
    path: Path | None = None,
) -> Path:
    errors = validate_e2e_live_first_green_record(record)
    if errors:
        raise ValueError("; ".join(errors))
    target = path or default_e2e_live_first_green_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def record_from_stub_template(stub_path: Path) -> dict[str, Any]:
    """Load stub JSON and validate shape (allows stub github_run_id for docs)."""
    data = json.loads(stub_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("stub must be a JSON object")
    return data
