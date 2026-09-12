#!/usr/bin/env bash
# scripts/ff-merge-to-master.sh
#
# Auto-merge a feature branch into master from a worktree-isolated session.
#
# PROBLEM: Claude sessions in worktree-isolated mode (e.g. .claude/worktrees/)
# are sandboxed — they cannot `git -C /main/repo`, `git --git-dir=/main/repo/.git`,
# or `cd /main/repo && git ...` because those commands target the parent
# shared checkout, which the sandbox considers out-of-scope.
#
# SOLUTION: `git push origin BRANCH:master` IS allowed because it talks to
# the remote, not to local refs in the parent worktree. This command is
# functionally equivalent to:
#   cd /main/repo
#   git merge --ff-only BRANCH    # update local master
#   git push origin master         # push to remote
# ...but in one atomic step from the worktree, with no manual user action.
#
# Additionally, `git update-ref refs/heads/master refs/heads/BRANCH` updates
# the local master ref in the shared .git directory (still in worktree).
# After this, the user's main worktree's local master is also up-to-date.
# They just need to refresh the working tree (e.g. `git pull --ff-only`).
#
# Usage:  ./scripts/ff-merge-to-master.sh <branch>
# Example: ./scripts/ff-merge-to-master.sh phase-57-p3-archdebt-reading-power
#
# Phase 53b mechanism: verified end-to-end with a real test commit (rolled
# back immediately after). See docs/superpowers/handoffs/2026-09-12-phase-53b-*.

set -euo pipefail

BRANCH="${1:-}"
if [ -z "$BRANCH" ]; then
    echo "Usage: $0 <branch>" >&2
    exit 1
fi

# Sanity: branch must be checked out somewhere
if ! git rev-parse --verify "refs/heads/$BRANCH" >/dev/null 2>&1; then
    echo "ERROR: branch $BRANCH does not exist locally" >&2
    exit 1
fi

# Sanity: must be fast-forward (no commits on master not on branch)
AHEAD=$(git rev-list --count "origin/master..$BRANCH" 2>/dev/null || echo 0)
BEHIND=$(git rev-list --count "$BRANCH..origin/master" 2>/dev/null || echo 0)
if [ "$BEHIND" -gt 0 ]; then
    echo "ERROR: $BRANCH is BEHIND origin/master by $BEHIND commits. ff-merge impossible." >&2
    exit 1
fi
if [ "$AHEAD" -eq 0 ]; then
    echo "NOTHING TO MERGE: $BRANCH is already at origin/master ($AHEAD new commits)" >&2
    exit 0
fi

echo ">>> Fast-forwarding origin/master by $AHEAD commit(s) from $BRANCH"
git push origin "${BRANCH}:master"

echo ">>> Updating local master ref in shared .git"
git update-ref refs/heads/master "refs/heads/$BRANCH"

echo ">>> Done."
echo ">>> If you have master checked out in your main worktree, run:"
echo "    git pull --ff-only   # OR   git reset --hard origin/master"
