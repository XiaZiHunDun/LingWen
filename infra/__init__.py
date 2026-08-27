"""灵文 infra 命名空间（Phase 18 薄壳）

仅保留 compat re-export: errors / config / util / schema。
其他子系统已迁到 packages/lingwen-*，请直接 import：
- from lingwen_core.agents.X import Y
- from lingwen_core.domain.X import Y
- from lingwen_core.use_cases.X import Y
- from lingwen_quality.X import Y
- from lingwen_storage.X import Y
"""
from infra.config import APIConfig
from infra.errors import BaseError, ValidationError
from infra.util import RetryConfig, retry, retry_async, with_retry

__all__ = [
    "APIConfig",
    "BaseError",
    "ValidationError",
    "RetryConfig",
    "retry",
    "retry_async",
    "with_retry",
]
