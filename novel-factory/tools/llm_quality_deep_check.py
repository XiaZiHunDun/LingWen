"""向后兼容 shim - 真实实现见 tools/llm_quality/

保留这个文件是为了让所有 6 个 import 站点、4 个 test patch 路径、
8 个文档调用的 `python tools/llm_quality_deep_check.py` 不需要修改。
"""
import sys
from pathlib import Path

# 让脚本运行模式下也能 import infra.* 和 tools.llm_quality
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.llm_quality import *  # noqa: F401,F403
from tools.llm_quality import (  # noqa: F401 - 显式 re-export
    LLMService, Issue, RepairResult, CheckerCache, FalsePositiveFilter,
    QualityReport, LLMQualityChecker, LLMRepairer,
    parse_chapter_range, save_report, main,
    run_phase_18a, run_phase_18b, run_phase_18c, run_phase_18d, run_phase_18e,
)

if __name__ == "__main__":
    main()
