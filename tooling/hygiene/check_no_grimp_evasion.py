"""Regression check: lingwen_llm.port_adapter MUST NOT contain any
grimp-evasion patterns (v16.5 invariant).

What we forbid:
- Static ``from infra.llm_service import ...`` (would re-trigger DP-02)
- String-concat dynamic imports of infra.llm_service (e.g. ``"infra" + "." + "llm" + "_service"``)
- PEP 562 ``__getattr__`` that re-exports infra.llm_service symbols

Why: v16.4 introduced these patterns as a workaround for grimp's
transitive-import detection. v16.5 eliminates them by relocating
LLMTask/TaskType to lingwen_shared and using a factory for the default
service. Future regressions that reintroduce any of these patterns
should fail this check.
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


def _read() -> str:
    return PORT_ADAPTER.read_text(encoding="utf-8")


def check_static_import() -> list[str]:
    """Fail if any static ``from infra.llm_service import`` exists."""
    text = _read()
    pattern = re.compile(r"^\s*from\s+infra\.llm_service\s+import\s+", re.MULTILINE)
    return [
        f"port_adapter.py:{m.start()}: forbidden static import `from infra.llm_service import ...`"
        for m in pattern.finditer(text)
    ]


def check_string_concat_evasion() -> list[str]:
    """Fail if ``infra.llm_service`` appears via string concatenation."""
    text = _read()
    # Match patterns like "infra" + "." + "llm" + "_service"
    pattern = re.compile(
        r'["\']infra["\']\s*\+\s*["\'][^"\']*["\']|"infra[^"\']*"\s*\+\s*["\']llm[^"\']*["\']|"llm"\s*\+\s*"_service"',
        re.MULTILINE,
    )
    return [
        f"port_adapter.py:{m.start()}: forbidden string-concat dynamic import of infra.llm_service"
        for m in pattern.finditer(text)
    ]


def check_pep562_re_export() -> list[str]:
    """Fail if a PEP 562 ``__getattr__`` function re-exports infra symbols.

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
    pattern = re.compile(r"infra\s*\.\s*llm_service")
    return [
        f"port_adapter.py:{m.start()}: forbidden PEP 562 re-export of "
        f"infra.llm_service (got rid of __getattr__ in v16.5)"
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
