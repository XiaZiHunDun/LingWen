#!/usr/bin/env bash
# Phase 13.0 T5 L6: shell slug env guard.
#
# Source this at top of any script that hardcodes a project slug:
#   source "$(dirname "$0")/_slug_guard.sh"
#
# Behavior:
#   - LINGWEN_PROJECT_ROOT unset  → exit 2 + [ERROR]
#   - LINGWEN_PROJECT_ROOT not a directory → exit 2 + [ERROR]
#   - LINGWEN_PROJECT_ROOT set + valid → set $PROJECT_ROOT, $SLUG (basename)
#
# Why: Phase 13.0 audit R4 — 6 scripts with hardcoded slugs silently used
# wrong project when CWD ≠ expected. Forcing env makes the mistake visible.
set -euo pipefail

if [[ -z "${LINGWEN_PROJECT_ROOT:-}" ]]; then
  echo "[ERROR] LINGWEN_PROJECT_ROOT 未设 — export LINGWEN_PROJECT_ROOT=/path/to/project" >&2
  echo "  例: export LINGWEN_PROJECT_ROOT=\"\$(pwd)/projects/anye-xinbiao\"" >&2
  exit 2
fi

if [[ ! -d "$LINGWEN_PROJECT_ROOT" ]]; then
  echo "[ERROR] LINGWEN_PROJECT_ROOT='$LINGWEN_PROJECT_ROOT' 不是目录" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$LINGWEN_PROJECT_ROOT" && pwd)"
SLUG="$(basename "$PROJECT_ROOT")"
