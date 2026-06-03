from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChapterContent:
    """章节内容封装"""
    chapter_num: int
    content: str
    uncertain_regions: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.content and len(self.content) > 5000:
            self.content = self.content[:5000]

@dataclass
class LLMIssue:
    """LLM检测结果"""
    chapter: int
    type: str
    description: str
    location: str = ""
    evidence: str = ""
    suggestion: str = ""
    severity: str = "P1"
