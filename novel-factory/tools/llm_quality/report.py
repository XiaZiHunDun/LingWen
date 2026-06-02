"""质检报告 - 单章检查输出

原 llm_quality_deep_check.py 第 32-54 行 QualityReport dataclass 独立出来。
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List


@dataclass
class QualityReport:
    """质检报告"""
    chapter: int
    checker: str
    issues: List = field(default_factory=list)
    score: float = 0.0
    llm_calls: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "chapter": self.chapter,
            "checker": self.checker,
            "issues": [asdict(i) for i in self.issues],
            "score": self.score,
            "llm_calls": self.llm_calls,
            "timestamp": self.timestamp
        }
