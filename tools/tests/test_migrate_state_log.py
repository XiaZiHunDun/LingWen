import json
import re
import subprocess
import sys
from pathlib import Path


def _run(script: Path, src: Path, dst: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), "--src", str(src), "--dst", str(dst)],
        capture_output=True, text=True,
    )


def test_migrate_minimal(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        '{"event": "DEFAULT_TEST", "data": {"k": "v"}, "source": "test"}\n'
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
    )
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    subprocess.run(
        [sys.executable, str(script), "--src", str(log), "--dst", str(out)],
        check=True,
    )
    lines = out.read_text().strip().split("\n")
    # DEFAULT_TEST 被丢弃 → 只剩一条 STEP_12 事件
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["step"] == "STEP_12"


def test_blank_lines_are_skipped(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        "\n"
        "{not json\n"
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
    )
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    result = _run(script, log, out)
    assert result.returncode == 0
    lines = [ln for ln in out.read_text().strip().split("\n") if ln]
    assert len(lines) == 1
    assert json.loads(lines[0])["step"] == "STEP_12"


def test_non_object_json_is_dropped(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        "[1,2,3]\n"
        "null\n"
        "42\n"
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
    )
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    result = _run(script, log, out)
    assert result.returncode == 0
    lines = [ln for ln in out.read_text().strip().split("\n") if ln]
    assert len(lines) == 1


def test_non_string_event_field_is_dropped(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        '{"event": ["nope"], "data": {}}\n'
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
    )
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    result = _run(script, log, out)
    assert result.returncode == 0
    lines = [ln for ln in out.read_text().strip().split("\n") if ln]
    assert len(lines) == 1


def test_missing_source_exits_zero_with_warning(tmp_path: Path):
    missing = tmp_path / "does_not_exist.log"
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    result = _run(script, missing, out)
    assert result.returncode == 0
    assert "warning" in result.stderr.lower()


def test_event_id_is_valid_ulid(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
    )
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    result = _run(script, log, out)
    assert result.returncode == 0
    line = out.read_text().strip()
    event = json.loads(line)
    assert re.match(r"^[0-9A-HJKMNP-TV-Z]{26}$", event["event_id"])


def test_actor_defaults_to_system_and_correlation_falls_back(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}}\n'
    )
    out = tmp_path / "events.jsonl"
    script = Path(__file__).resolve().parents[1] / "migrate_state_log.py"
    result = _run(script, log, out)
    assert result.returncode == 0
    event = json.loads(out.read_text().strip())
    assert event["actor"] == "system"
    assert event["correlation_id"] == "migrate"
    assert event["payload"]["raw_event"] == "STEP_BUMP"
