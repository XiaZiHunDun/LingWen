"""向后兼容 shim - 真实实现见 tools/llm_quality/

保留这个文件是为了让现有 4 个 import 站点(infra/cli/commands/check.py
LLM 集成 + tests/tools/test_llm_quality_deep_check.py 的 test patch 路径)
继续工作,以及 `python tools/llm_quality_deep_check.py` 脚本入口。

历史: 1138L 单文件 → tools/llm_quality/ 子包(5 文件 + __init__.py)。

本 shim 只 re-export 真正被外部 import 的 4 个名字:
- main:           脚本入口 `python tools/llm_quality_deep_check.py`
- LLMService:     test patch 路径(LLMService 替换 mock)
- LLMQualityChecker: check 命令 + test 实际构造 checker
- QualityReport:  test 实际构造 report

其余 12 个名字(Issue/RepairResult/CheckerCache/FalsePositiveFilter/
LLMRepairer/parse_chapter_range/save_report/run_phase_18{a,b,c,d,e})
已无人通过本 shim 路径 import,需用时直接 `from tools.llm_quality import`。
"""
import sys
from pathlib import Path

# 让脚本运行模式下也能 import infra.* 和 tools.llm_quality
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.llm_quality import (  # noqa: F401
    LLMQualityChecker,
    LLMService,
    QualityReport,
    main,
)

if __name__ == "__main__":
    main()
