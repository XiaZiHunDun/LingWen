"""
Phase 15.0 T2.7: dashboard-side ReadingPowerDB 兼容 shim.

消除历史债 `dashboard/helpers/reading_power_db.py` 截断副本,
改用 `infra.reading_power.db.ReadingPowerDB`, 保留 `init_if_missing` 兼容签名.

设计:
- dashboard 调用方仍可传 `init_if_missing=False` 跳过 _ensure_db_path
- 内部委托给 infra 版 (infra 版无 init_if_missing, 但会自动 ensure + init_db)
- 弃用警告: 引导 caller 改用 `from infra.reading_power.db import ReadingPowerDB`
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

# Re-export infra 版 (canonical)
from infra.reading_power.db import ReadingPowerDB as _InfraReadingPowerDB


class ReadingPowerDB(_InfraReadingPowerDB):
    """Phase 15.0 T2.7: dashboard 兼容 shim, 直接继承 infra 版.

    保留 dashboard 端 `init_if_missing` 签名以兼容既有 caller.
    实际 init 逻辑 (ensure path + create tables) 走 infra 版.
    """

    DB_PATH = Path(__file__).parent.parent / ".state" / "reading_power.db"

    def __init__(
        self,
        db_path: Optional[Path] = None,
        init_if_missing: bool = True,
    ):
        # 发出弃用警告 (T2.7 提示 caller 切到 infra 版)
        warnings.warn(
            "Phase 15.0 T2.7: dashboard.helpers.reading_power_db 是历史 shim, "
            "请改用 from infra.reading_power.db import ReadingPowerDB. "
            "init_if_missing 参数被忽略 (infra 版总会 ensure).",
            DeprecationWarning,
            stacklevel=2,
        )
        # 解析 db_path, 委托给 infra 版
        resolved_path = db_path or self.DB_PATH
        # 透传 init_if_missing 参数给 infra 版
        super().__init__(db_path=resolved_path, init_if_missing=init_if_missing)
