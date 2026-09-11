"""lingwen-result — canonical Result type package.

Phase 45 P3-ARCHDEBT: relocated from infra/result.py (168 LOC).
TRUE LEAF (0 workspace deps; stdlib only: typing).
"""

from __future__ import annotations

from lingwen_result.service import (
    Err,
    Ok,
    Result,
    combine,
    either,
    err,
    from_optional,
    ok,
    wrap,
)

__all__ = [
    "Ok",
    "Err",
    "Result",
    "ok",
    "err",
    "wrap",
    "from_optional",
    "combine",
    "either",
]