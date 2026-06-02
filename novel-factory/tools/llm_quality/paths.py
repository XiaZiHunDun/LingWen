"""路径常量 - 单一所有者

原 llm_quality_deep_check.py 第 23-24 行的 PROJECT_ROOT / sys.path 集中到这里，
避免子模块重复计算路径。子模块用 `from . import paths` 引用，便于 monkeypatch。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
