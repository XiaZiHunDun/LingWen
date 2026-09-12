#!/usr/bin/env bash
# scripts/lingwen-ensure-auto-merge.sh
#
# Idempotent launcher: ensures the lingwen-auto-merge background daemon
# is running. If not, starts it. Safe to call repeatedly.
#
# Called by Claude at the start of each phase to guarantee the
# 0-manual-merge workflow is in place. Does not require the user to
# do anything (auto-heals after machine reboot, manual kill, etc.).
#
# Usage: ./scripts/lingwen-ensure-auto-merge.sh

DAEMON="/home/ailearn/.claude/scripts/lingwen-auto-merge.sh"
PIDFILE="/tmp/lingwen-auto-merge.pid"
LOG="/tmp/lingwen-auto-merge.log"

# Already running? exit.
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "lingwen-auto-merge already running (pid=$(cat "$PIDFILE"))"
    exit 0
fi

# Start it
rm -f "$LOG"
nohup "$DAEMON" > /dev/null 2>&1 &
sleep 1
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "lingwen-auto-merge started (pid=$(cat "$PIDFILE"))"
else
    echo "lingwen-auto-merge FAILED to start; check $LOG"
    exit 1
fi
