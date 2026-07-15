#!/usr/bin/env bash
# Phase 11.11: verify per-module coverage floors after pytest --cov.
# Requires .coverage in project root (run pytest with --cov first).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .coverage ]]; then
  echo "ERROR: .coverage not found — run pytest with --cov=infra --cov=tools --cov=dashboard first" >&2
  exit 1
fi

python - <<'PY'
import sys
from coverage import Coverage

from infra.coverage_gate import evaluate_module_gate, format_module_gate_report

cov = Coverage(config_file="pyproject.toml", data_file=".coverage")
cov.load()
report = evaluate_module_gate(cov)
print(format_module_gate_report(report))
sys.exit(0 if report["passed"] else 1)
PY
