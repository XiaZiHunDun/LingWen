"""向后兼容 shim - 真实实现见 tools/llm_quality/

保留这个文件是为了让现有 2 个 import 站点
(packages/lingwen-cli/src/lingwen_cli/commands/check.py LLM 集成 +
`python tools/llm_quality_deep_check.py` 脚本入口) 继续工作。

历史: 1138L 单文件 → tools/llm_quality/ 子包(5 文件 + __init__.py)。

本 shim 只 re-export 真正被外部 import 的 3 个名字:
- main:           脚本入口 `python tools/llm_quality_deep_check.py`
- LLMQualityChecker: check 命令构造 checker
- QualityReport:  QualityReport 实例化

Phase 53b fix: removed stale `LLMService` re-export. That symbol does
NOT exist in the new subpackage (renamed to `LLMServiceAdapter` from
`lingwen_llm.port_adapter` during the Phase 5 LLM_QUALITY split). The
shim's `from tools.llm_quality import LLMService` was raising
ImportError on import, breaking the shim entirely.

Tests that previously patched `tools.llm_quality_deep_check.LLMService`
must now either:
- Use canonical `tools.llm_quality.LLMServiceAdapter` directly
- Or mock-inject via `LLMQualityChecker(llm_service=mock)` constructor

Phase 53b C2 migrates the test file accordingly.
"""

import sys
from pathlib import Path

# 让脚本运行模式下也能 import infra.* 和 tools.llm_quality
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.llm_quality import (  # noqa: F401
    LLMQualityChecker,
    QualityReport,
    main,
)

if __name__ == "__main__":
    main()
