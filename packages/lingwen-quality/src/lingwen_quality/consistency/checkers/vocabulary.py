"""
R2-012: 战斗/修真/视觉 词汇表 — 跨 checker 共享

之前 ABSTRACT_CULTIVATION (16 项) / CONCRETE_VISUAL (25 项) /
CONCRETE_ACTION (18 项) 都硬编码在 BattleVisualizationChecker 类体里。
其他需要类似词表的 checker (e.g. sentence_diversity, ai_gloss) 只能
复制粘贴,词汇会随时间漂移。

修复:词汇表迁出至本模块,BattleVisualizationChecker 通过类属性引用
(保持原有 API,调用方零改动)。新增 checker 直接 import。
"""
from __future__ import annotations

from typing import List

# 抽象修炼/能量概念 — 修真/玄幻小说里常被过度使用,缺乏视觉冲击
ABSTRACT_CULTIVATION: List[str] = [
    "星辰能量",
    "能量波动",
    "灵气",
    "虚无",
    "暗能量",
    "神秘力量",
    "一股力量",
    "某种力量",
    "能量",
    "气场",
    "气势",
    "威压",
    "力量涌动",
    "力量流转",
    "能量汇聚",
    "能量爆发",
]

# 具象视觉描写 — 视觉可感知的物体/光/烟/血
CONCRETE_VISUAL: List[str] = [
    "光芒",
    "火焰",
    "血",
    "碎片",
    "声响",
    "声音",
    "碎屑",  # R2-012: 修复前与上面"碎片"重复,已去重
    "尘埃",
    "烟雾",
    "血泊",
    "伤口",
    "伤痕",
    "焦黑",
    "裂痕",
    "裂缝",
    "倒下",
    "后退",
    "跌倒",
    "翻滚",
    "迸发",
    "溅出",
    "喷涌",
    "炸开",
    "碎裂",
    "火星",  # R2-013: 修复 test_mixed_content_ratio — 测试文案把"火星"作具象
]

# 具象动作描写 — 单字动词,直接可感知的攻击/位移
CONCRETE_ACTION: List[str] = [
    "砍",
    "劈",
    "刺",
    "斩",
    "割",
    "划",
    "砸",
    "摔",
    "踢",
    "踹",
    "撞",
    "推",
    "拉",
    "扯",
    "撕",
    "抓",
    "掐",
    "扼",
]
