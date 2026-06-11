from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class UnifiedOptions:
    """统一选项定义 - 所有命令共享的基础选项"""
    range: List[int] = field(default_factory=list)
    parallel: int = 4
    verbose: bool = False
    dry_run: bool = False
    output: Optional[str] = None


@dataclass
class CheckOptions(UnifiedOptions):
    """check 命令选项"""
    quick: bool = False
    full: bool = False
    llm: bool = False
    limit: int = 20


@dataclass
class RepairOptions(UnifiedOptions):
    """repair 命令选项"""
    track: str = "all"
    regression: bool = False


@dataclass
class VerifyOptions(UnifiedOptions):
    """verify 命令选项"""
    repaired: bool = False
    compare: Optional[str] = None


@dataclass
class PolishOptions(UnifiedOptions):
    """polish 命令选项"""
    chapter: Optional[int] = None
    key_type: Optional[str] = None
    auto_detect: bool = False


@dataclass
class StoryContractOptions(UnifiedOptions):
    """story-contract 命令选项"""
    genre: Optional[str] = None
    chapter: Optional[int] = None
    persist: bool = False
    query: str = ""


@dataclass
class AntiTropeOptions(UnifiedOptions):
    """anti-trope 命令选项"""
    outline: str = ""
    count: int = 3
    format: bool = True


@dataclass
class LLMAnalyzeOptions(UnifiedOptions):
    """llm-analyze 命令选项"""
    chapter: Optional[int] = None
    issue_file: Optional[str] = None


@dataclass
class BackfillOptions(UnifiedOptions):
    """backfill 命令选项 (Phase 9.11 CVG backfill + Phase 9.12 LLM opt-in)"""
    # NOTE: 默认 dry_run=True, 跟 UnifiedOptions 默认 False 反过来.
    # Per 主公 Q4 decision: 默认 dry-run (0 写库, 仅 print 统计).
    dry_run: bool = True
    vol: Optional[int] = None
    rules: Optional[str] = None  # path to extraction_rules.yaml
    corpus_root: Optional[str] = None  # Phase 9.33: override chapter corpus path
    # Phase 9.12 additive: LLM opt-in (默认 0 走, 走 Phase 9.11 rule path, 0 cost)
    use_llm: bool = False
    apply: bool = False  # --apply 强需 --use-llm (rule path 用 --execute)
    cache_path: Optional[Path] = None  # LLMCache 路径 (None → ~/.cache/lingwen/llm_cache.json)
    llm_confidence_threshold: Optional[int] = None  # None → scanner_calibration.yaml
    calibration_path: Optional[str] = None  # Phase 9.34: override calibration yaml


@dataclass
class RippleAuditOptions(UnifiedOptions):
    """ripple-audit 命令选项 (Phase 9.14).

    Reads ripple_audit history for 1 ripple. 0 改 storage / 0 启动 dashboard。
    """
    ripple_id: str = ""
    limit: int = 20  # max audit entries to print (newest first)


@dataclass
class RippleRollbackOptions(UnifiedOptions):
    """ripple-rollback 命令选项 (Phase 9.14).

    Soft-rollback applied/rejected ripple → pending + audit entry.
    --reason 强需 (storage layer 也会 double-check 空字符串)。
    """
    ripple_id: str = ""
    reason: str = ""  # required, non-empty
    actor: str = "cli:lingwen-ripple"


@dataclass
class RippleResetOptions(UnifiedOptions):
    """ripple-reset 命令选项 (Phase 9.18).

    Idempotent reset ripple status (test/dev tool).
    跟既 ripple-rollback 1:1 风格, 但 origin='system' (test tool, 0 user action)。
    """
    ripple_id: str = ""
    to_status: str = ""  # required, one of 5 valid statuses


@dataclass
class CascadeOptions(UnifiedOptions):
    """cascade 命令选项 (Phase 9.19 + 9.20 + 9.21).

    Re-run cascade BFS with caller-specified max_depth (not persisted by default).
    Phase 9.21 NEW: action dispatch ('run' | 'cancel') + cancel-specific fields.
    1:1 with ripple-audit pattern.
    """
    ripple_id: str = ""
    max_depth: int = 3  # 1..10
    max_nodes_cap: int = 100  # Phase 9.32 F16: 1..1000 BFS node cap
    persist: bool = False  # Phase 9.20 NEW: 持久化 cascade run 到 cascade_runs 表 (off by default)
    # Phase 9.21 NEW: subparser group dispatch
    action: str = "run"      # 'run' | 'cancel' | 'migrate'
    run_id: int = 0          # for cancel action
    reason: str = ""         # for cancel action (logged + WS payload, not persisted)
    # Phase 9.36 F21: migrate action
    execute: bool = False    # migrate --execute (default dry-run)
    migrate_ripple_id: str | None = None  # optional filter


@dataclass
class RippleScanOptions(UnifiedOptions):
    """ripple-scan 命令选项 (Phase 9.34 F19 calibration)."""
    calibrate: bool = False
    yaml_example: bool = False  # Phase 9.43 F32: print suggested yaml snippet
    gold_path: Optional[Path] = None
    fixture_dir: Optional[Path] = None
    calibration: Optional[Path] = None
    chapter: int = 1
