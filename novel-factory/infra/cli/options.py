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