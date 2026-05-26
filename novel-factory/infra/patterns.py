"""
全局正则表达式模式注册表（单例）
"""
import re
from typing import Dict, List, Optional, Tuple

Pattern = re.Pattern


class PatternRegistry:
    """
    全局正则表达式模式注册表（单例）
    """

    _instance = None
    _patterns: Dict[str, Pattern] = {}

    _SENTENCE_PATTERNS = {
        'dialog': (r'「[^」]+」', 'dialog', '对话句'),
        'dialog_english': (r'"[^"]+"', 'dialog_english', '对话句(英文)'),
        'narrate_he': (r'他[说问道喊叫笑叹谓称著显示露出透露出冒][^「"。，！？]*[。！？]?', 'narrate_he', '他述句'),
        'narrate_she': (r'她[说问道喊叫笑叹谓称著显示露出透露出冒][^「"。，！？]*[。！？]?', 'narrate_she', '她述句'),
        'voice_desc': (r'声音[低沉急促平静冷淡愤怒]?[^。！？]*[。！？]?', 'voice_desc', '声音描写'),
        'action_verb': (r'[伸收抬举握拿抓拉推踢打杀砍劈刺剪拆拔扔掉丢接住送打翻拉抽鼓起迈跨踏冲]+[^。！？]*[。！？]?', 'action_verb', '动词动作句'),
        'perception': (r'[看听闻尝感到觉得意识到发现]+[^。！？]*[。！？]?', 'perception', '感知句'),
        'heart_desc': (r'心头[^。！？]*[。！？]?', 'heart_desc', '心头描写'),
        'env_dusk': (r'黄昏[将染成变作]?[^。！？]*[。！？]?', 'env_dusk', '黄昏描写'),
        'env_night': (r'夜色[降临笼罩弥漫充满]?[^。！？]*[。！？]?', 'env_night', '夜色描写'),
    }

    _AI_TRACE_PATTERNS = {
        'template_first': (r'首先', 'ai_trace', 'AI模板词'),
        'template_second': (r'其次', 'ai_trace', 'AI模板词'),
        'template_third': (r'最后', 'ai_trace', 'AI模板词'),
        'conjunction_therefore': (r'因此', 'ai_trace', 'AI连接词'),
        'conjunction_however': (r'然而', 'ai_trace', 'AI转折词'),
        'conjunction_thus': (r'于是', 'ai_trace', 'AI顺承词'),
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._compile_all()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "PatternRegistry":
        return cls()

    def _compile_all(self):
        for name, (pattern, _, _) in self._SENTENCE_PATTERNS.items():
            try:
                self._patterns[name] = re.compile(pattern)
            except re.error:
                pass

        for name, (pattern, _, _) in self._AI_TRACE_PATTERNS.items():
            try:
                self._patterns[name] = re.compile(pattern)
            except re.error:
                pass

    def get(self, name: str) -> Optional[Pattern]:
        return self._patterns.get(name)

    def list_patterns(self) -> List[str]:
        return list(self._patterns.keys())