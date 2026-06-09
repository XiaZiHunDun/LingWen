from dataclasses import dataclass, field
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
    """backfill 命令选项 (Phase 9.11 CVG backfill)"""
    # NOTE: 默认 dry_run=True, 跟 UnifiedOptions 默认 False 反过来.
    # Per 主公 Q4 decision: 默认 dry-run (0 写库, 仅 print 统计).
    dry_run: bool = True
    vol: Optional[int] = None
    rules: Optional[str] = None  # path to extraction_rules.yaml
