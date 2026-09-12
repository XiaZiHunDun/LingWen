"""
lingwen-reading-power — Reading Power System (追读力系统).

Phase 57 P3-ARCHDEBT: relocated from ``infra/reading_power/`` to
``packages/lingwen-reading-power/`` as a workspace member. The canonical
import path is ``lingwen_reading_power.*`` (NOT ``infra.reading_power.*``).

Provides 8 public classes for chapter-level analysis of Chinese web novels:
- ReadingPowerDB       — SQLite CRUD for hooks/coolpoints/chapter_summary/analysis_log
- ReadingPowerEngine   — Orchestrator (rule-scan → optional LLM → store → summary)
- RuleMatcher          — YAML-driven regex scanning
- SuspectedSegment     — NamedTuple returned by RuleMatcher.scan (canonical)
- LLMAnalyzer          — Prompt-based deep classification via injected ai_service
- AnalysisResult       — Dataclass returned by LLMAnalyzer.analyze
- HookTracker          — Persistence wrapper around save_hook/get_hooks
- CoolPointTracker     — Persistence wrapper around save_coolpoint/get_coolpoints

NOT-LEAF package — 2 workspace deps:
- lingwen-shared     (ConnectionPort protocol)
- lingwen-storage    (SqliteStorageAdapter — runtime deferred in db._get_connection)

External deps: pyyaml.

The DB_PATH constant in db.py uses ``parents[N]`` to reach the repo root for
``.state/reading_power.db``. After Phase 57 relocation to
``packages/lingwen-reading-power/src/lingwen_reading_power/db.py``, this
needs ``parents[4]`` (Phase 40a C1.5 fixup applied in C1.5).
"""

from lingwen_reading_power.coolpoint_tracker import CoolPointTracker
from lingwen_reading_power.db import ReadingPowerDB
from lingwen_reading_power.engine import ReadingPowerEngine
from lingwen_reading_power.hook_tracker import HookTracker
from lingwen_reading_power.llm_analyzer import AnalysisResult, LLMAnalyzer
from lingwen_reading_power.rule_matcher import RuleMatcher, SuspectedSegment

__all__ = [
    "ReadingPowerDB",
    "ReadingPowerEngine",
    "RuleMatcher",
    "SuspectedSegment",
    "LLMAnalyzer",
    "AnalysisResult",
    "HookTracker",
    "CoolPointTracker",
]