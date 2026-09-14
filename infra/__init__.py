"""灵文 infra 命名空间（Phase 18 薄壳）

仅保留 compat re-export: errors / config / schema。
其他子系统已迁到 packages/lingwen-*，请直接 import：
- from lingwen_core.agents.X import Y
- from lingwen_core.domain.X import Y
- from lingwen_core.use_cases.X import Y
- from lingwen_quality.X import Y
- from lingwen_storage.X import Y

注：util (RetryConfig + retry + retry_async + with_retry + is_transient_error + backoff_delay) 于 Phase 82 P3-ARCHDEBT 全量迁移至 packages/lingwen-util/，已不属于本 compat re-export。
"""

from lingwen_errors import BaseError, ValidationError

from lingwen_config import APIConfig
from lingwen_util import RetryConfig, retry, retry_async, with_retry

__all__ = [
    "APIConfig",
    "BaseError",
    "ValidationError",
    "RetryConfig",
    "retry",
    "retry_async",
    "with_retry",
]
