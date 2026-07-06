#!/usr/bin/env bash
# Start LingWen Dashboard for Cursor SSH remote access (forward port 5173 on Windows).
# Delegates to dashboard-daemon.sh so processes survive Cursor restarts.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/scripts/dashboard-daemon.sh" start
