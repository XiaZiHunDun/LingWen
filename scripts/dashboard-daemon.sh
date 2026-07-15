#!/usr/bin/env bash
# LingWen Dashboard 守护进程：与 Cursor 终端解耦，Cursor 重启后仍可访问。
# Usage:
#   bash scripts/dashboard-daemon.sh start|stop|restart|status
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT/.run"
LOG_DIR="$ROOT/logs/dashboard"
API_PID_FILE="$RUN_DIR/api.pid"
VITE_PID_FILE="$RUN_DIR/vite.pid"
API_PORT="${DASHBOARD_PORT:-8765}"
VITE_PORT="${VITE_PORT:-5173}"
API_HOST="${DASHBOARD_HOST:-0.0.0.0}"

mkdir -p "$RUN_DIR" "$LOG_DIR"
unset LINGWEN_PROJECT_ROOT

api_url() { echo "http://127.0.0.1:${API_PORT}/api/health"; }
cvg_url() { echo "http://127.0.0.1:${API_PORT}/api/cvg/ripples?limit=1"; }
vite_url() { echo "http://127.0.0.1:${VITE_PORT}/"; }

is_api_up() { curl -sf "$(api_url)" >/dev/null 2>&1; }
is_cvg_up() { curl -sf --max-time 5 "$(cvg_url)" >/dev/null 2>&1; }
is_vite_up() { curl -sf "$(vite_url)" >/dev/null 2>&1; }

pid_alive() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

read_pid() {
  local file="$1"
  [[ -f "$file" ]] || return 1
  tr -d '[:space:]' < "$file"
}

stop_pid_file() {
  local file="$1"
  local label="$2"
  local pid
  pid="$(read_pid "$file" 2>/dev/null || true)"
  if pid_alive "$pid"; then
    echo "Stopping $label (pid $pid) ..."
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      pid_alive "$pid" || break
      sleep 0.25
    done
    if pid_alive "$pid"; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$file"
}

start_api() {
  if is_api_up; then
    echo "API already healthy on :${API_PORT}"
    return 0
  fi
  local pid
  pid="$(read_pid "$API_PID_FILE" 2>/dev/null || true)"
  if pid_alive "$pid"; then
    echo "Waiting for API (pid $pid) ..."
  else
    echo "Starting API on ${API_HOST}:${API_PORT} ..."
    cd "$ROOT"
    setsid nohup env \
      DASHBOARD_HOST="$API_HOST" \
      DASHBOARD_PORT="$API_PORT" \
      LINGWEN_DASHBOARD_DEV=1 \
      python dashboard/app.py >>"$LOG_DIR/api.log" 2>&1 </dev/null &
    echo $! >"$API_PID_FILE"
  fi
  for _ in $(seq 1 40); do
    if is_api_up; then
      echo "API ready: $(api_url)"
      return 0
    fi
    sleep 0.25
  done
  echo "ERROR: API failed to start. See $LOG_DIR/api.log" >&2
  tail -n 20 "$LOG_DIR/api.log" 2>/dev/null || true
  return 1
}

start_vite() {
  if is_vite_up; then
    echo "Vite already healthy on :${VITE_PORT}"
    return 0
  fi
  local pid
  pid="$(read_pid "$VITE_PID_FILE" 2>/dev/null || true)"
  if pid_alive "$pid"; then
    echo "Waiting for Vite (pid $pid) ..."
  else
    echo "Starting Vite on 0.0.0.0:${VITE_PORT} ..."
    cd "$ROOT/dashboard/frontend"
    setsid nohup pnpm dev --host 0.0.0.0 --port "$VITE_PORT" >>"$LOG_DIR/vite.log" 2>&1 </dev/null &
    echo $! >"$VITE_PID_FILE"
  fi
  for _ in $(seq 1 60); do
    if is_vite_up; then
      echo "Vite ready: $(vite_url)"
      return 0
    fi
    sleep 0.25
  done
  echo "ERROR: Vite failed to start. See $LOG_DIR/vite.log" >&2
  tail -n 20 "$LOG_DIR/vite.log" 2>/dev/null || true
  return 1
}

cmd_start() {
  start_api
  start_vite
  echo ""
  echo ">>> Cursor SSH: 转发端口 ${VITE_PORT}（开发）或 ${API_PORT}（单端口模式）"
  echo ">>> 打开: http://localhost:${VITE_PORT}/"
  echo ">>> 日志: $LOG_DIR/{api,vite}.log"
  echo ">>> 管理: bash scripts/dashboard-daemon.sh status|stop|restart"
}

cmd_stop() {
  stop_pid_file "$VITE_PID_FILE" "Vite"
  stop_pid_file "$API_PID_FILE" "API"
  echo "Dashboard stopped."
}

cmd_status() {
  local api_pid vite_pid
  api_pid="$(read_pid "$API_PID_FILE" 2>/dev/null || echo "-")"
  vite_pid="$(read_pid "$VITE_PID_FILE" 2>/dev/null || echo "-")"
  if is_api_up; then
    echo "API  : UP   :${API_PORT} (pid ${api_pid})"
    if is_cvg_up; then
      echo "CVG  : UP   ripples"
    else
      echo "CVG  : DOWN ripples (try: bash scripts/dashboard-daemon.sh restart)"
    fi
  else
    echo "API  : DOWN :${API_PORT} (pid ${api_pid})"
  fi
  if is_vite_up; then
    echo "Vite : UP   :${VITE_PORT} (pid ${vite_pid})"
  else
    echo "Vite : DOWN :${VITE_PORT} (pid ${vite_pid})"
  fi
  if is_api_up && is_vite_up; then
    return 0
  fi
  return 1
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start
}

ACTION="${1:-start}"
case "$ACTION" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_restart ;;
  status) cmd_status ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}" >&2
    exit 1
    ;;
esac
