import json
from pathlib import Path
import subprocess
import sys


def test_migrate_minimal(tmp_path: Path):
    log = tmp_path / "state_history.log"
    log.write_text(
        '{"event": "DEFAULT_TEST", "data": {"k": "v"}, "source": "test"}\n'
        '{"event": "STEP_BUMP", "data": {"step": "STEP_12"}, "source": "agent"}\n'
    )
    out = tmp_path / "events.jsonl"
    script = (Path(__file__).resolve().parents[1] / "migrate_state_log.py").as_posix()
    subprocess.run(
        [sys.executable, script, "--src", str(log), "--dst", str(out)],
        check=True,
    )
    lines = out.read_text().strip().split("\n")
    # DEFAULT_TEST 被丢弃 → 只剩一条 STEP_12 事件
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["step"] == "STEP_12"