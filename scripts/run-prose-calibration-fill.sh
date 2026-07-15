#!/usr/bin/env bash
# Phase 12.04: fill prose calibration log with assisted verdicts (留/删/疑).
# Usage: bash scripts/run-prose-calibration-fill.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
chmod +x "$0" 2>/dev/null || true

python3 - <<'PY'
import os
from datetime import date
from pathlib import Path

from infra.prose_calibration import list_primary_revision_slugs
from infra.prose_calibration_overrides import load_all_calibration_overrides
from infra.prose_judge import build_calibration_round, render_calibration_log_document

root = Path.cwd()
overrides = load_all_calibration_overrides()
rounds = []
for slug in list_primary_revision_slugs():
    project = root / "projects" / slug
    rounds.append(build_calibration_round(slug, project, overrides=overrides))

llm_note = (
    "> **LLM judge**：本地未配置 `MINIMAX_API_KEY` 时跳过 `--llm` 刷新；"
    "CI Secret 可用时在 Actions 跑 `run-prose-judge.sh <slug> --llm`。"
)
if all(r.get("judge_source") == "llm" for r in rounds):
    llm_note = (
        "> **LLM judge**：七书 `prose-judge-report.json` 已为 **source=llm**；"
        "verdict 仍由规则交叉信号辅助，可人工覆写。"
    )
elif os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
    llm_note = "> **LLM judge**：API key 已配置，可 `bash scripts/run-prose-judge.sh --save-all --llm` 刷新。"

doc = render_calibration_log_document(
    rounds,
    round_label=str(date.today()),
    operator="run-prose-calibration-fill.sh (assisted)",
    llm_note=llm_note,
)

out = root / "docs" / "prose-calibration-log.md"
out.write_text(doc, encoding="utf-8")
total = sum(r["stats"]["total"] for r in rounds)
mis = sum(r["stats"]["misreport_count"] for r in rounds)
rate = round(100.0 * mis / total, 1) if total else 0
print(f"[write] {out.relative_to(root)} — {total} samples, misreport {rate}%")
PY
