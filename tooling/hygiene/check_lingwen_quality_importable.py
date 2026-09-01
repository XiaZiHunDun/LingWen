#!/usr/bin/env python3
"""CI regression guard for lingwen_quality package symbol availability.

Closes the v15.7.1 carryover claim "lingwen_quality module missing" by asserting
that key symbols are importable from the canonical lingwen_quality.* modules.
If any symbol disappears (package move, accidental rename, etc.), this guard
fails CI — preventing the "missing" claim from re-emerging in CLAUDE.md.

Exit codes:
- 0: all symbols importable
- 1: at least one symbol/module failed to import

Symbols verified (canonical source: docs/superpowers/specs/2026-09-01-phase-126-v16-5-n16-v15-7-1-debt-closure-design.md):
- IssueSeverity, Issue, IssueLocation, CheckerType
- ConsistencyEngine, ConsistencyArbitrator
- CheckerInspector, ForeshadowChecker, PacingChecker
- SceneTransitionChecker, DialogueAuthenticityChecker
- CreativeWhitelist
"""
import importlib
import sys

# Modules that must be importable (cheap existence check, no symbol probing)
REQUIRED_MODULES = [
    "lingwen_quality",
    "lingwen_quality.consistency",
    "lingwen_quality.consistency.engine",
    "lingwen_quality.consistency.engine.data_structures",
    "lingwen_quality.consistency.engine.consistency_engine",
    "lingwen_quality.consistency.engine.consistency_arbitrator",
    # NOTE: checker_inspector lives in engine/, not checkers/ (discovery during T1.2).
    "lingwen_quality.consistency.engine.checker_inspector",
    "lingwen_quality.consistency.checkers",
    "lingwen_quality.consistency.checkers.foreshadow_checker",
    "lingwen_quality.consistency.checkers.pacing_checker",
    "lingwen_quality.consistency.checkers.scene_transition_checker",
    "lingwen_quality.consistency.checkers.dialogue_authenticity_checker",
    "lingwen_quality.consistency.creative_whitelist",
    "lingwen_quality.quality",
]


# Symbols that must exist in one of the canonical modules
# Each entry: (symbol_name, list of (module_path, attribute_name) tuples to search)
REQUIRED_SYMBOLS = {
    "IssueSeverity": ["lingwen_quality.consistency.engine.data_structures"],
    "Issue": ["lingwen_quality.consistency.engine.data_structures"],
    "IssueLocation": ["lingwen_quality.consistency.engine.data_structures"],
    "CheckerType": ["lingwen_quality.consistency.engine.data_structures"],
    "ConsistencyEngine": ["lingwen_quality.consistency.engine.consistency_engine"],
    "ConsistencyArbitrator": ["lingwen_quality.consistency.engine.consistency_arbitrator"],
    # NOTE: CheckerInspector lives in engine/, not checkers/.
    "CheckerInspector": ["lingwen_quality.consistency.engine.checker_inspector"],
    "ForeshadowChecker": ["lingwen_quality.consistency.checkers.foreshadow_checker"],
    "PacingChecker": ["lingwen_quality.consistency.checkers.pacing_checker"],
    "SceneTransitionChecker": ["lingwen_quality.consistency.checkers.scene_transition_checker"],
    "DialogueAuthenticityChecker": ["lingwen_quality.consistency.checkers.dialogue_authenticity_checker"],
    "CreativeWhitelist": ["lingwen_quality.consistency.creative_whitelist"],
}


def main() -> int:
    failures: list[str] = []

    # Check modules
    for module_path in REQUIRED_MODULES:
        try:
            importlib.import_module(module_path)
        except ImportError as exc:
            failures.append(f"Module {module_path!r}: ImportError: {exc}")

    # Check symbols
    for symbol_name, candidate_modules in REQUIRED_SYMBOLS.items():
        found = False
        for module_path in candidate_modules:
            try:
                module = importlib.import_module(module_path)
            except ImportError:
                continue
            if hasattr(module, symbol_name):
                found = True
                break
        if not found:
            failures.append(
                f"Symbol {symbol_name!r}: not found in any of {candidate_modules}"
            )

    if failures:
        print("lingwen_quality importability check FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(
        f"lingwen_quality importability check PASSED "
        f"({len(REQUIRED_MODULES)} modules + {len(REQUIRED_SYMBOLS)} symbols verified)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
