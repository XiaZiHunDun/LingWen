"""Creator batch history helpers — failure reason labels for dashboard."""
from __future__ import annotations

from typing import Any


def derive_batch_failure_reason(job: dict[str, Any]) -> str | None:
    """Return a short failure reason label for failed batch jobs."""
    if str(job.get("status", "")).lower() != "failed":
        return None
    error = str(job.get("error") or "").strip()
    if error:
        return error[:160]
    exit_code = job.get("exit_code")
    if exit_code is not None:
        return f"进程退出码 {exit_code}"
    return "未知失败"


def enrich_batch_history_job(job: dict[str, Any]) -> dict[str, Any]:
    """Attach failure_reason when applicable."""
    row = dict(job)
    reason = derive_batch_failure_reason(row)
    if reason:
        row["failure_reason"] = reason
    if row.get("retry_count") is None:
        row["retry_count"] = 0
    return row
