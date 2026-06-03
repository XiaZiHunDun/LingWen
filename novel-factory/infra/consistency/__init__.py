# consistency package
"""
一致性保障系统

提供小说写作过程中的一致性检查功能，包括：
- 角色一致性检查
- 物品连续性检查
- 时间线合理性检查
- 能力一致性检查
- 人设稳定性检查
- 伏笔回收检查
- 大纲偏离度检查
- AI痕迹检测
"""

from .engine.consistency_engine import ConsistencyEngine
from .engine.report_generator import ReportGenerator

__all__ = ["ConsistencyEngine", "ReportGenerator"]
