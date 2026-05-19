"""软性评分器 - 方向H质量工具集"""

from quality_tools.soft_scorers.base import BaseScorer, ScoredResult

from quality_tools.soft_scorers.tension import TensionScorer
from quality_tools.soft_scorers.emotion import EmotionScorer
from quality_tools.soft_scorers.prose_vitality import ProseVitalityScorer
from quality_tools.soft_scorers.voice_consistency import VoiceConsistencyScorer
from quality_tools.soft_scorers.dialogue import DialogueScorer
from quality_tools.soft_scorers.theme_integration import ThemeIntegrationScorer
from quality_tools.soft_scorers.redundancy import RedundancyScorer
from quality_tools.soft_scorers.transition import TransitionScorer
from quality_tools.soft_scorers.scene_purpose import ScenePurposeScorer
from quality_tools.soft_scorers.symbolism import SymbolismScorer

__all__ = [
    "BaseScorer",
    "ScoredResult",
    "TensionScorer",
    "EmotionScorer",
    "ProseVitalityScorer",
    "VoiceConsistencyScorer",
    "DialogueScorer",
    "ThemeIntegrationScorer",
    "RedundancyScorer",
    "TransitionScorer",
    "ScenePurposeScorer",
    "SymbolismScorer",
]