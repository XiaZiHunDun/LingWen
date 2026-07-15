"""Phase 9.98 F90: ci_records helpers."""
from __future__ import annotations

import json

import pytest

from infra.agent_system.ci_records import (
    build_e2e_live_first_green_record,
    default_e2e_live_first_green_path,
    validate_e2e_live_first_green_record,
    write_e2e_live_first_green_record,
)


class TestCiRecordsF90:
    def test_build_and_validate_record(self):
        record = build_e2e_live_first_green_record(
            github_run_id="1234567890",
            github_run_url="https://github.com/XiaZiHunDun/LingWen/actions/runs/1234567890",
            operator="tester",
            notes="pytest",
        )
        assert validate_e2e_live_first_green_record(record) == []
        assert record["tests_passed"] == 5
        assert record["local_parity"]["passed"] is True

    def test_validate_rejects_missing_local_parity(self):
        errors = validate_e2e_live_first_green_record({"record_id": "x"})
        assert any("local_parity" in e for e in errors)

    def test_write_record_to_tmp_path(self, tmp_path):
        record = build_e2e_live_first_green_record(
            github_run_id="local-parity-pending-remote",
            github_run_url="https://github.com/XiaZiHunDun/LingWen/actions/workflows/test.yml",
            operator="pytest",
        )
        path = tmp_path / "e2e-live-first-green.json"
        write_e2e_live_first_green_record(record, path=path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["github_run_id"] == "local-parity-pending-remote"
        assert validate_e2e_live_first_green_record(loaded) == []

    def test_default_path_under_ci_records(self):
        path = default_e2e_live_first_green_path()
        assert path.name == "e2e-live-first-green.json"
        assert path.parent.name == "ci_records"

    def test_stub_template_shape(self, tmp_path):
        stub = tmp_path / "stub.json"
        stub.write_text(
            json.dumps({
                "record_id": "e2e-live-first-green-stub",
                "workflow": "test.yml",
                "trigger": "push",
                "branch": "master",
                "github_run_id": "0000000000",
                "github_run_url": "https://github.com/XiaZiHunDun/LingWen/actions/runs/0000000000",
                "job_name": "Playwright live-backend (5 specs)",
                "tests_passed": 5,
                "summary_phrase": "Playwright live-backend — passed",
                "local_parity": {
                    "script": "novel-factory/scripts/verify-e2e-live-ci.sh",
                    "passed": True,
                    "verified_at": "2026-06-11T12:00:00Z",
                },
                "operator": "stub-example",
                "recorded_at": "2026-06-11T12:00:00Z",
            }),
            encoding="utf-8",
        )
        data = json.loads(stub.read_text(encoding="utf-8"))
        assert validate_e2e_live_first_green_record(data) == []
