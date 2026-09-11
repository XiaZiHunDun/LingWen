"""Regression check: lingwen_llm.port_adapter MUST NOT contain any
grimp-evasion patterns (v16.5 invariant).

What we forbid:
- Static ``from infra.llm_service import ...`` or
  ``from lingwen_llm_service import ...`` (would re-trigger DP-02)
- String-concat dynamic imports of infra.llm_service or lingwen_llm_service
  (e.g. ``"infra" + "." + "llm" + "_service"``)
- PEP 562 ``__getattr__`` that re-exports infra.llm_service or
  lingwen_llm_service symbols

Why: v16.4 introduced these patterns as a workaround for grimp's
transitive-import detection. v16.5 eliminates them by relocating
LLMTask/TaskType to lingwen_shared and using a factory for the default
service. Phase 43 P3-ARCHDEBT relocates infra.llm_service.py to
lingwen_llm_service package — the forbidden pattern now blocks BOTH
old and new paths. Future regressions that reintroduce any of these
patterns should fail this check.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PORT_ADAPTER = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "lingwen-llm"
    / "src"
    / "lingwen_llm"
    / "port_adapter.py"
)

# Phase 43: regex covers both infra.llm_service (legacy) and
# lingwen_llm_service (canonical) — business code MUST NOT touch either.
_LLM_SERVICE_RE = r"(?:infra\.llm_service|lingwen_llm_service)"

# Literal placeholder for f-string braces — avoids Python expression eval.
_MODULE_PLACEHOLDER = "{infra.llm_service|lingwen_llm_service}"


def _read() -> str:
    return PORT_ADAPTER.read_text(encoding="utf-8")


def check_static_import() -> list[str]:
    """Fail if any static ``from infra.llm_service import`` or
    ``from lingwen_llm_service import`` exists."""
    text = _read()
    pattern = re.compile(rf"^\s*from\s+{_LLM_SERVICE_RE}\s+import\s+", re.MULTILINE)
    return [
        f"port_adapter.py:{m.start()}: forbidden static import `from {_MODULE_PLACEHOLDER} import ...`"
        for m in pattern.finditer(text)
    ]


def check_string_concat_evasion() -> list[str]:
    """Fail if ``infra.llm_service`` or ``lingwen_llm_service`` appears via string concatenation."""
    text = _read()
    # Match patterns like "infra" + "." + "llm" + "_service" (and lingwen variant)
    pattern = re.compile(
        r'["\']infra["\']\s*\+\s*["\'][^"\']*["\']|"infra[^"\']*"\s*\+\s*["\']llm[^"\']*["\']|"llm"\s*\+\s*"_service"|["\']lingwen["\']\s*\+\s*["\']_llm_service["\']|"lingwen_llm"\s*\+\s*"_service"',
        re.MULTILINE,
    )
    return [
        f"port_adapter.py:{m.start()}: forbidden string-concat dynamic import of {_MODULE_PLACEHOLDER}"
        for m in pattern.finditer(text)
    ]


def check_pep562_re_export() -> list[str]:
    """Fail if a PEP 562 ``__getattr__`` function re-exports infra/lingwen symbols.

    Note: matches ``def __getattr__(...)`` (a function definition) rather
    than the substring ``__getattr__``. The port_adapter module's
    architectural-invariant docstring literally mentions ``__getattr__``
    as part of describing what must NOT exist; a substring check would
    fire on the docstring itself.
    """
    text = _read()
    getattr_def = re.search(r"^\s*def\s+__getattr__\s*\(", text, re.MULTILINE)
    if not getattr_def:
        return []
    pattern = re.compile(_LLM_SERVICE_RE)
    return [
        f"port_adapter.py:{m.start()}: forbidden PEP 562 re-export of "
        f"{_MODULE_PLACEHOLDER} (got rid of __getattr__ in v16.5)"
        for m in pattern.finditer(text)
    ]


def main() -> int:
    findings = check_static_import() + check_string_concat_evasion() + check_pep562_re_export()
    if findings:
        print("FAIL: grimp-evasion regression detected in port_adapter.py:")
        for f in findings:
            print(f"  {f}")
        return 1
    print("OK: port_adapter.py is grimp-evasion-free")
    return 0


if __name__ == "__main__":
    sys.exit(main())