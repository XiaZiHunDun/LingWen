"""LLM 深度质检工具包 - PHASE_5_LLM_QUALITY

拆分自原 tools/llm_quality_deep_check.py (1138L)：

  report.py      - QualityReport dataclass
  checker.py     - LLMQualityChecker (4 个 check 方法)
  repairer.py    - LLMRepairer (9 个 repair 方法 + 上下文路由)
  phases.py      - 4 个 run_phase_18X 阶段调度 + run_phase_18e
  cli.py         - 参数解析 + 报告保存 + main 入口

使用方式：
  from tools.llm_quality import LLMQualityChecker, LLMRepairer, QualityReport
  python -m tools.llm_quality --help
"""
from infra.cache import CheckerCache
from infra.filter import FalsePositiveFilter
from infra.llm_service import LLMService
from infra.quality import Issue, RepairResult

from .checker import LLMQualityChecker
from .cli import main, parse_chapter_range, save_report
from .phases import run_phase_18a, run_phase_18b, run_phase_18c, run_phase_18d, run_phase_18e
from .repairer import LLMRepairer
from .report import QualityReport

__all__ = [
    "LLMService", "Issue", "RepairResult", "CheckerCache", "FalsePositiveFilter",
    "QualityReport", "LLMQualityChecker", "LLMRepairer",
    "parse_chapter_range", "save_report", "main",
    "run_phase_18a", "run_phase_18b", "run_phase_18c", "run_phase_18d", "run_phase_18e",
]
