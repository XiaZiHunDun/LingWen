"""InitProjectResult dataclass + module-level patterns/consts.

Migrated from infra/project_init.py — see invariant #56.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

# (chapter_num, title, overview, events, foreshadow)
_MINIMAL_BEATS: tuple[tuple[int, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        1,
        "异常信号",
        "主角在日常中撞见无法解释的第一处异常，故事钩子落下。",
        ("主角在熟悉场景中察觉违和细节", "做出第一个主动追查的决定"),
        ("异常来源", "代价"),
    ),
    (
        2,
        "第一条线索",
        "追查带来具体线索，也带来第一个风险。",
        ("线索指向被忽略的旧事", "配角或对手首次露面"),
        ("旧事的真相",),
    ),
    (
        3,
        "踏入迷雾",
        "第一幕收束：主角跨过不可逆的门槛。",
        ("主角为真相付出可见代价", "确立本章核心矛盾"),
        ("门槛之后无退路",),
    ),
    (
        4,
        "压力升级",
        "对抗面扩大，计划第一次受挫。",
        ("外部阻力显性化", "主角尝试用旧办法解决新问题并失败"),
        ("真正对手",),
    ),
    (
        5,
        "裂缝",
        "团队/关系出现裂缝，信息并不完整。",
        ("信任被试探", "次要真相揭露但误导方向"),
        ("谎言", "背叛可能"),
    ),
    (
        6,
        "真相一角",
        "中段揭示：答案的一部分成立，但更糟的可能浮现。",
        ("关键证据出现", "主角意识到自己曾误判"),
        ("更大的图景",),
    ),
    (
        7,
        "最低点",
        "希望被打碎，主角必须重新定义目标。",
        ("失去重要之物或立场", "做出艰难取舍"),
        ("重生",),
    ),
    (
        8,
        "抉择",
        "主角选择承担代价，走向终局。",
        ("明确最终行动方案", "与对手或困境正面对峙"),
        ("终局伏笔",),
    ),
    (
        9,
        "高潮",
        "核心冲突爆发并给出阶段性答案。",
        ("高潮对决或认知对决", "主题句在行动中落地"),
        ("余波",),
    ),
    (
        10,
        "余波",
        "短篇收束：回答「所以呢」，留下适度余韵。",
        ("处理高潮后果", "给出情感与主题上的落点"),
        ("开放或闭合",),
    ),
)


@dataclass(frozen=True)
class InitProjectResult:
    slug: str
    title: str
    root: Path
    chapter_count: int
    creation_mode: str
    files_written: tuple[str, ...]
