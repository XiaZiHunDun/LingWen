"""Phase 9.11: 4-dim rule-based extractors for CVG backfill.

公开 API (跟 spec 5.1 一致):
- CharacterExtractor: character 维 (regex 中文名 + alias_map + blacklist + threshold)
- ForeshadowExtractor: foreshadow 维 (keyword + chapter_window 聚合)
- SettingExtractor: setting 维 (regex 名词后缀)
- PlotPointExtractor: plot_point 维 (大纲 ## 标题抽取)
"""
from infra.cross_volume.extractors.character_extractor import CharacterExtractor
from infra.cross_volume.extractors.foreshadow_extractor import ForeshadowExtractor
from infra.cross_volume.extractors.setting_extractor import SettingExtractor
from infra.cross_volume.extractors.plot_point_extractor import PlotPointExtractor

__all__ = [
    "CharacterExtractor",
    "ForeshadowExtractor",
    "SettingExtractor",
    "PlotPointExtractor",
]
