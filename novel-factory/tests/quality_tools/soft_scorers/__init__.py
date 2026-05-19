"""软性评分器 - 方向H质量工具集"""

from soft_scorers.base import BaseScorer, ScoredResult

from soft_scorers.tension import TensionScorer
from soft_scorers.emotion import EmotionScorer
from soft_scorers.prose_vitality import ProseVitalityScorer
from soft_scorers.voice_consistency import VoiceConsistencyScorer
from soft_scorers.dialogue import DialogueScorer
from soft_scorers.theme_integration import ThemeIntegrationScorer
from soft_scorers.redundancy import RedundancyScorer
from soft_scorers.transition import TransitionScorer
from soft_scorers.scene_purpose import ScenePurposeScorer
from soft_scorers.symbolism import SymbolismScorer

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