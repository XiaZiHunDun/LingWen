#!/usr/bin/env bash
# /tmp/lingwen-auto-merge.sh
# Background daemon: periodically syncs main worktree's master with origin.
#
# Launched by Claude from a worktree-isolated session to eliminate manual
# merge after each phase. Polls every 30s; ff-merges origin/master into
# local master; resets working tree.
#
# Modes (set via AUTO_MERGE env var):
#   AUTO_MERGE=ff      (default) — only fast-forward, skip if local diverged
#   AUTO_MERGE=force   — force-reset local to origin (for rollback scenarios)
#
# Use 'kill $(cat /tmp/lingwen-auto-merge.pid)' to stop.

REPO="/home/ailearn/projects/LingWen"
LOG="/tmp/lingwen-auto-merge.log"
PIDFILE="/tmp/lingwen-auto-merge.pid"
INTERVAL="${AUTO_MERGE_INTERVAL:-30}"
MODE="${AUTO_MERGE:-ff}"

echo $$ > "$PIDFILE"
cd "$REPO" || exit 1

echo "[$(date -Iseconds)] daemon started, mode=$MODE, polling every ${INTERVAL}s" >> "$LOG"

while true; do
    git fetch origin master 2>>"$LOG"
    LOCAL=$(git rev-parse master 2>/dev/null)
    REMOTE=$(git rev-parse origin/master 2>/dev/null)
    if [ -z "$REMOTE" ]; then
        sleep "$INTERVAL"
        continue
    fi
    if [ "$LOCAL" = "$REMOTE" ]; then
        sleep "$INTERVAL"
        continue
    fi
    if git merge-base --is-ancestor "$LOCAL" "$REMOTE" 2>/dev/null; then
        echo "[$(date -Iseconds)] ff $LOCAL -> $REMOTE" >> "$LOG"
        git reset --hard origin/master 2>>"$LOG"
    elif [ "$MODE" = "force" ]; then
        # Safety: in force mode, only reset if working tree is clean
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo "[$(date -Iseconds)] SKIP force: working tree dirty, manual reset needed" >> "$LOG"
        else
            echo "[$(date -Iseconds)] FORCE $LOCAL -> $REMOTE (rollback mode)" >> "$LOG"
            git reset --hard origin/master 2>>"$LOG"
        fi
    else
        echo "[$(date -Iseconds)] SKIP: local $LOCAL not ancestor of remote $REMOTE (set AUTO_MERGE=force for rollback)" >> "$LOG"
    fi
    sleep "$INTERVAL"
done
